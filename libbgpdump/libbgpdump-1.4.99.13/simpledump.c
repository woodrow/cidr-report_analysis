/*
 Copyright (c) 2007 - 2010 RIPE NCC - All Rights Reserved

 Permission to use, copy, modify, and distribute this software and its
 documentation for any purpose and without fee is hereby granted, provided
 that the above copyright notice appear in all copies and that both that
 copyright notice and this permission notice appear in supporting
 documentation, and that the name of the author not be used in advertising or
 publicity pertaining to distribution of the software without specific,
 written prior permission.

 THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
 ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS; IN NO EVENT SHALL
 AUTHOR BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
 DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN
 AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

Parts of this code have been engineered after analiyzing GNU Zebra's
source code and therefore might contain declarations/code from GNU
Zebra, Copyright (C) 1999 Kunihiro Ishiguro. Zebra is a free routing
software, distributed under the GNU General Public License. A copy of
this license is included with libbgpdump.

Author: Dan Ardelean (dan@ripe.net)
*/

#include "bgpdump_lib.h"
#include "bgpdump_attr.h"
#include <stdbool.h>
#include <time.h>

#include <stdlib.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include <unistd.h>
#include <stdio.h>
#include <argp.h>

/* SRW ADDITIONS **************************************************************/

extern BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE *table_dump_v2_peer_index_table;

#define PREFIX_CLASS_LONELY     1
#define PREFIX_CLASS_TOP        2
#define PREFIX_CLASS_DEAGG      3
#define PREFIX_CLASS_DELEG      4

typedef struct struct_TREE_NODE TREE_NODE;

struct struct_TREE_NODE {
    BGPDUMP_IP_ADDRESS  *prefix;
    u_char              prefix_len;

    struct aspath       *as_path;

    TREE_NODE           *ms_0;  // more specific with next bit = 0
    TREE_NODE           *ms_1;  // more specific with next bit = 1
    bool                is_aggregable;
                        // # of aggregable prefixes beneath this prefix
    u_int               aggregable_more_specifics;
    u_char              prefix_class;  // one of PREFIX_CLASS_*
};

void init_tree_node(TREE_NODE *t);
void init_tree_node_pl(TREE_NODE *t, BGPDUMP_IP_ADDRESS *prefix, u_char prefix_len);
void init_tree_node_l(TREE_NODE *t, char prefix_len);
bool add_node_to_tree(TREE_NODE *root, TREE_NODE *new);
void update_ancestor(TREE_NODE *ancestor, TREE_NODE *descendant);
bool as_path_match(TREE_NODE *a, TREE_NODE *b);

void init_tree_node(TREE_NODE *t) {
    if(t != NULL) {
        t->prefix = NULL;
        t->prefix_len = 0;
        t->as_path = NULL;
        t->ms_0 = NULL;
        t->ms_1 = NULL;
        t->is_aggregable = true;
        t->aggregable_more_specifics = 0;
        t->prefix_class = PREFIX_CLASS_LONELY;
    }
}

void init_tree_node_pl(TREE_NODE *t, BGPDUMP_IP_ADDRESS *prefix,
        u_char prefix_len) {
    if(t != NULL) {
        init_tree_node(t);
        t->prefix = prefix;
        t->prefix_len = prefix_len;
    }
}

void init_tree_node_l(TREE_NODE *t, char prefix_len) {
    if(t != NULL) {
        init_tree_node(t);
        t->prefix_len = prefix_len;
    }
}

bool add_node_to_tree(TREE_NODE *root, TREE_NODE *new) {
    TREE_NODE *cursor = root;
    u_int test_mask = 0x80000000;
    char i;
    for(i = 0; i < new->prefix_len; i++) {
        update_ancestor(cursor, new);
        if(new->prefix->v4_addr.s_addr & test_mask) {
            if(cursor->ms_1 == NULL) {
                if(i == new->prefix_len-1) {
                    cursor->ms_1 = new;
                    return true;
                } else {
                    cursor->ms_1 = malloc(sizeof(TREE_NODE));
                    init_tree_node_l(cursor->ms_1, i+1);
                }
            }
            cursor = cursor->ms_1;
        } else {
            if(cursor->ms_0 == NULL) {
                if(i == new->prefix_len-1) {
                    cursor->ms_0 = new;
                    return true;
                } else {
                    cursor->ms_0 = malloc(sizeof(TREE_NODE));
                    init_tree_node_l(cursor->ms_1, i+1);
                }
            }
            cursor = cursor->ms_0;
        }
        test_mask >>= 1;
    }
    return false; // this should never happen -- major problem
}

void update_ancestor(TREE_NODE *ancestor, TREE_NODE *descendant) {
    if(descendant->prefix != NULL && ancestor->prefix != NULL) {
        if(ancestor->prefix_class == PREFIX_CLASS_LONELY) {
            ancestor->prefix_class = PREFIX_CLASS_TOP;
        }
        if(as_path_match(ancestor, descendant)) {
            descendant->prefix_class = PREFIX_CLASS_DEAGG;
            if(descendant->is_aggregable) {
                ancestor->aggregable_more_specifics++;
            }
        } else {
            ancestor->prefix_class = PREFIX_CLASS_DELEG;
            ancestor->is_aggregable = false;
            ancestor->aggregable_more_specifics = 0;
        }
    }
}

bool as_path_match(TREE_NODE *a, TREE_NODE *b) {
    return false;
}

/*****************************************************************************/

const char *argp_program_version =
   "table_dumper 0.1";
 const char *argp_program_bug_address =
   "<woodrow@mit.edu>";

 /* Program documentation. */
 static char doc[] =
   "table_dumper -- dumps or otherwise does interesting things to MRT BGP tables in the context of CIDR Report analysis";

 /* A description of the arguments we accept. */
 static char args_doc[] = "MRT_INPUT OUTPUT";

 /* The options we understand. */
 static struct argp_option options[] = {
   {"dump-table", 'd', "VANTAGE-AS", 0,
   "Output all routes observed from peer VANTAGE-AS in 'prefix AS_PATH' format. This argument may be omitted to output routes from all ASes present in the table."},
   {"peer-ips", 'p', 0, 0,
   "Include peer IPs in the table dump produced, providing 'prefix peer_ip AS_PATH' output instead."},
   { 0 }
 };

 /* Used by main to communicate with parse_opt. */
 struct arguments
 {
   char *args[2];                /* arg1 & arg2 */
   int peer_ips;
   as_t dump_vantage_as;
 };

 /* Parse a single option. */
 static error_t
 parse_opt (int key, char *arg, struct argp_state *state)
 {
   /* Get the input argument from argp_parse, which we
      know is a pointer to our arguments structure. */
   struct arguments *arguments = state->input;
   char *endptr;

   switch (key)
     {
     case 'd':
       arguments->dump_vantage_as = (as_t)strtol(arg, &endptr, 10);
       if(arg == endptr)
         argp_error(state, "Invalid format for AS vantage point.");
       break;
     case 'p':
       arguments->peer_ips = 1;
       break;

     case ARGP_KEY_ARG:
       if (state->arg_num >= 2)
         /* Too many arguments. */
         argp_usage (state);

       arguments->args[state->arg_num] = arg;

       break;

     case ARGP_KEY_END:
       if (state->arg_num < 2)
         /* Not enough arguments. */
         argp_usage (state);
       break;

     default:
       return ARGP_ERR_UNKNOWN;
     }
   return 0;
 }

 /* Our argp parser. */
 static struct argp argp = { options, parse_opt, args_doc, doc };

/* END ADDITIONS **************************************************************/


    void dump_table(BGPDUMP_ENTRY *entry, struct arguments arguments, FILE *outfile);
    void show_attr(attributes_t *attr);
    void show_prefixes(int count,struct prefix *prefix);
#ifdef BGPDUMP_HAVE_IPV6
    void show_v6_prefixes(int count, struct prefix *prefix);
#endif

int main(int argc, char **argv) {
    BGPDUMP *my_dump;
    BGPDUMP_ENTRY *my_entry=NULL;
    FILE *outfile = NULL;

    // argument parsing
    struct arguments arguments;
    /* Default values. */
    arguments.peer_ips = 0;
    arguments.dump_vantage_as = 0;
    argp_parse (&argp, argc, argv, 0, 0, &arguments);

    my_dump=bgpdump_open_dump(arguments.args[0]);
    if(my_dump==NULL) {
        printf("Error opening MRT dump file ...\n");
        exit(1);
    }

    if(strncmp(arguments.args[1], "-", 1) == 0) {
        outfile = stdout;
    } else {
        outfile = fopen(arguments.args[1], "w");
        if(outfile == NULL) {
            printf("Error opening output file ...\n");
            exit(1);
        }
    }

    do {
        my_entry=bgpdump_read_next(my_dump);
        if(my_entry!=NULL) {
            dump_table(my_entry, arguments, outfile);
            bgpdump_free_mem(my_entry);
        }
    } while(my_dump->eof==0);

    fclose(outfile);
    bgpdump_close_dump(my_dump);
    return 0;
}

void dump_table(BGPDUMP_ENTRY *entry, struct arguments arguments, FILE *outfile) {
    char prefix[BGPDUMP_ADDRSTRLEN], peer_ip[BGPDUMP_ADDRSTRLEN];
    int i;
	BGPDUMP_TABLE_DUMP_V2_PREFIX *e;
	as_t vantage_as = arguments.dump_vantage_as;
	int peer_ips = arguments.peer_ips;

    switch(entry->type) {
	case BGPDUMP_TYPE_MRTD_TABLE_DUMP:
	    if(vantage_as && entry->body.mrtd_table_dump.peer_as != vantage_as) {
	        break;
	    }
        if(entry->subtype == AFI_IP) {
            strcpy(prefix,
                inet_ntoa(entry->body.mrtd_table_dump.prefix.v4_addr));
            strcpy(peer_ip,
                inet_ntoa(entry->body.mrtd_table_dump.peer_ip.v4_addr));

            if((entry->attr->flag &
                ATTR_FLAG_BIT(BGP_ATTR_AS_PATH)) !=0) {
                if(peer_ips) {
                    fprintf(outfile,
                            "%s/%d %s %s\n",
                            prefix, entry->body.mrtd_table_dump.mask, peer_ip, entry->attr->aspath->str);
                } else {
                    fprintf(outfile,
                            "%s/%d %s\n",
                            prefix, entry->body.mrtd_table_dump.mask, entry->attr->aspath->str);
                }
            }
        } /*else {
            //unknown AFI
            printf("Error: MRT_TABLE_DUMP with unknown AFI.\n");
            break;
        }*/
	    break;

	case BGPDUMP_TYPE_TABLE_DUMP_V2:
        e = &entry->body.mrtd_table_dump_v2_prefix;

        if(e->afi == AFI_IP) {
            strcpy(prefix, inet_ntoa(e->prefix.v4_addr));

            for(i = 0; i < e->entry_count; i++){
                if(vantage_as && e->entries[i].peer->peer_as != vantage_as) {
                    continue;
                }
                if(e->entries[i].peer->afi == AFI_IP){
                    inet_ntop(AF_INET, &e->entries[i].peer->peer_ip, peer_ip, INET6_ADDRSTRLEN);

                    if((e->entries[i].attr->flag &
                        ATTR_FLAG_BIT(BGP_ATTR_AS_PATH)) !=0) {
                        if(peer_ips) {
                            fprintf(outfile,
                                    "%s/%d %s %s\n",
                                    prefix, e->prefix_length, peer_ip, e->entries[i].attr->aspath->str);
                        } else {
                            fprintf(outfile,
                                    "%s/%d %s\n",
                                    prefix, e->prefix_length, e->entries[i].attr->aspath->str);
                        }
                    }
                }
            }
        } /*else {
            printf("Error: MRT_TABLE_DUMP_V2 entry with unknown subtype.\n");
            break;
        }*/
	    break;

	/*default:
	    printf("TYPE            : Unknown %d\n", entry->type);
        show_attr(entry->attr);*/
    }
}
