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

    void dump_table(BGPDUMP_ENTRY *entry, as_t vantage_as, FILE *outfile);
    void show_attr(attributes_t *attr);
    void show_prefixes(int count,struct prefix *prefix);
#ifdef BGPDUMP_HAVE_IPV6
    void show_v6_prefixes(int count, struct prefix *prefix);
#endif

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
   {"list-peers", 'l', 0, 0,
   "Output a list of all peer ASes seen in this dump"},
   {"dump-table", 'd', "VANTAGE-AS", 0,
   "Output all routes observed from peer VANTAGE-AS in 'prefix AS_PATH' format"},
   { 0 }
 };

 /* Used by main to communicate with parse_opt. */
 struct arguments
 {
   char *args[2];                /* arg1 & arg2 */
   int list_peers, verbose;
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
     case 'l':
       arguments->list_peers = 1;
       break;
     case 'd':
       arguments->dump_vantage_as = (as_t)strtol(arg, &endptr, 10);
       if(arg == endptr)
           argp_error(state, "Invalid format for AS vantage point.");
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

     case ARGP_KEY_SUCCESS:
         if((arguments->list_peers != 1) &&
            (arguments->dump_vantage_as == 0))
            argp_error(state, "You must select at least one processing action");
         if((arguments->list_peers == 1) &&
            (arguments->dump_vantage_as != 0))
            argp_error(state, "You must select at most one processing action");

     default:
       return ARGP_ERR_UNKNOWN;
     }
   return 0;
 }

 /* Our argp parser. */
 static struct argp argp = { options, parse_opt, args_doc, doc };

/* END ADDITIONS **************************************************************/

int main(int argc, char **argv) {
    BGPDUMP *my_dump;
    BGPDUMP_ENTRY *my_entry=NULL;
    FILE *outfile = NULL;
    char done_processing = 0;

    // argument parsing
    struct arguments arguments;
    /* Default values. */
    arguments.list_peers = 0;
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

    if(arguments.dump_vantage_as > 0) {
//        printf("Dumping table from vantage point %u...\n", arguments.dump_vantage_as);
        do {
            my_entry=bgpdump_read_next(my_dump);
            if(my_entry!=NULL) {
                dump_table(my_entry, arguments.dump_vantage_as,
                           outfile);
                bgpdump_free_mem(my_entry);
            }
        } while(my_dump->eof==0);
    }
    if(arguments.list_peers) {
//        printf("Listing peers...\n");
        while(my_dump->eof==0) {
            my_entry=bgpdump_read_next(my_dump);
            if(my_entry!=NULL) {
                if(table_dump_v2_peer_index_table) {
                    BGPDUMP_TABLE_DUMP_V2_PEER_INDEX_TABLE *t;
                    t = table_dump_v2_peer_index_table;
                    int i;
                    for(i = 0; i < t->peer_count; i++) {
                        fprintf(outfile, "%u %s\n", t->entries[i].peer_as, inet_ntoa(t->entries[i].peer_ip.v4_addr));
                    }
                    done_processing = 1;
                } else {
                    // do stuff for non-indexed table
                    // go through and create a table of unique (AS, IP) peer pairs
                }
                bgpdump_free_mem(my_entry);
                break;
            }
        }
        if(!done_processing) {
            while(my_dump->eof==0) {
                my_entry=bgpdump_read_next(my_dump);
                if(my_entry!=NULL) {
                    // do stuff for non-indexed table
                    bgpdump_free_mem(my_entry);
                }
            }
        }
    }
    fclose(outfile);

    bgpdump_close_dump(my_dump);
//fprintf(stderr, "%s: OK=%d, BAD=%d (%f%% OK)\n", my_dump->filename, my_dump->parsed_ok, my_dump->parsed - my_dump->parsed_ok, (float) my_dump->parsed_ok / my_dump->parsed * 100);

 return 0;
}

void dump_table(BGPDUMP_ENTRY *entry, as_t vantage_as, FILE *outfile) {
    char prefix[BGPDUMP_ADDRSTRLEN], peer_ip[BGPDUMP_ADDRSTRLEN];
//    char source_ip[BGPDUMP_ADDRSTRLEN], destination_ip[BGPDUMP_ADDRSTRLEN];
//    struct mp_nlri *mp_announce, *mp_withdraw;
    int i;
//    int code, subcode;
	BGPDUMP_TABLE_DUMP_V2_PREFIX *e;

    //printf("TIME            : %s",asctime(gmtime(&entry->time)));
    switch(entry->type) {
	case BGPDUMP_TYPE_MRTD_TABLE_DUMP:
	    if(entry->body.mrtd_table_dump.peer_as != vantage_as) {
	        break;
	    }
        if(entry->subtype == AFI_IP) {
        strcpy(prefix, inet_ntoa(entry->body.mrtd_table_dump.prefix.v4_addr));
        strcpy(peer_ip, inet_ntoa(entry->body.mrtd_table_dump.peer_ip.v4_addr));
#ifdef BGPDUMP_HAVE_IPV6
        } else if(entry->subtype == AFI_IP6) {
        inet_ntop(AF_INET6, &entry->body.mrtd_table_dump.prefix.v6_addr, prefix,
              sizeof(prefix));
        inet_ntop(AF_INET6, &entry->body.mrtd_table_dump.peer_ip.v6_addr, peer_ip,
              sizeof(peer_ip));
#endif
        } else {
            //unknown AFI
            printf("Error: MRT_TABLE_DUMP with unknown AFI.\n");
            break;
        }
        /* printf("TYPE            : BGP Table Dump Entry\n");
        printf("    VIEW        : %d\n",entry->body.mrtd_table_dump.view);
        printf("    SEQUENCE    : %d\n",entry->body.mrtd_table_dump.sequence);
        printf("    PREFIX      : %s/%d\n",prefix,entry->body.mrtd_table_dump.mask);
        printf("    STATUS      : %d\n",entry->body.mrtd_table_dump.status);
        printf("    UPTIME      : %s",asctime(gmtime(&entry->body.mrtd_table_dump.uptime)));
        printf("    PEER IP     : %s\n",peer_ip);
        printf("    PEER AS     : %u\n",entry->body.mrtd_table_dump.peer_as);
        show_attr(entry->attr); */
	    break;

	case BGPDUMP_TYPE_TABLE_DUMP_V2:
        e = &entry->body.mrtd_table_dump_v2_prefix;

        if(e->afi == AFI_IP) {
            strcpy(prefix, inet_ntoa(e->prefix.v4_addr));
#ifdef BGPDUMP_HAVE_IPV6
        } else if(e->afi == AFI_IP6) {
            inet_ntop(AF_INET6, &e->prefix.v6_addr, prefix, INET6_ADDRSTRLEN);
#endif
        } else {
            printf("Error: MRT_TABLE_DUMP_V2 entry with unknown subtype.\n");
            break;
        }

        for(i = 0; i < e->entry_count; i++){
            if(e->entries[i].peer->peer_as != vantage_as) {
                continue;
            }
            if((e->entries[i].attr->flag & ATTR_FLAG_BIT(BGP_ATTR_AS_PATH)) !=0)
                fprintf(outfile,
                        "%s/%d %s\n",
                        prefix, e->prefix_length, e->entries[i].attr->aspath->str);


/*             if(i){
                printf("\nTIME            : %s",asctime(gmtime(&entry->time)));
                printf("LENGTH          : %u\n", entry->length);
            }


            printf("TYPE            : BGP Table Dump version 2 Entry\n");
            printf("    SEQUENCE    : %d\n",e->seq);
            printf("    PREFIX      : %s/%d\n",prefix,e->prefix_length);

            if(e->entries[i].peer->afi == AFI_IP){
                inet_ntop(AF_INET, &e->entries[i].peer->peer_ip, peer_ip, INET6_ADDRSTRLEN);
#ifdef BGPDUMP_HAVE_IPV6
            } else if (e->entries[i].peer->afi == AFI_IP6){
                inet_ntop(AF_INET6, &e->entries[i].peer->peer_ip, peer_ip, INET6_ADDRSTRLEN);
#endif
            } else {
                sprintf(peer_ip, "N/A, unsupported AF");
            }
            printf("    PEER IP     : %s\n",peer_ip);
            printf("    PEER AS     : %u\n",e->entries[i].peer->peer_as);

            show_attr(e->entries[i].attr); */
        }

	    break;

	default:
	    printf("TYPE            : Unknown %d\n", entry->type);
    	show_attr(entry->attr);

    }
}

void show_attr(attributes_t *attr) {
    int have_nexthop = 0;
    printf("ATTRIBUTES      :\n");

    if(attr != NULL) {
	    printf("   ATTR_LEN     : %d\n",attr->len);

	    if( (attr->flag & ATTR_FLAG_BIT (BGP_ATTR_ORIGIN) ) !=0 )		printf("   ORIGIN       : %d\n",attr->origin);
	    else printf("   ORIGIN       : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_AS_PATH) ) !=0)		printf("   ASPATH       : %s\n",attr->aspath->str);
	    else printf("   ASPATH       : N/A\n");

	    printf("   NEXT_HOP     : ");
	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_NEXT_HOP) ) !=0) {
		have_nexthop = 1;
		printf("%s", inet_ntoa(attr->nexthop));
	    }

#ifdef BGPDUMP_HAVE_IPV6
	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_MP_REACH_NLRI)) &&
	         MP_IPV6_ANNOUNCE(attr->mp_info) != NULL) {
		char addr[INET6_ADDRSTRLEN];
		struct mp_nlri *mp_nlri = MP_IPV6_ANNOUNCE(attr->mp_info);
		u_int8_t len = mp_nlri->nexthop_len;

		if(have_nexthop)
		    printf(" ");

		have_nexthop = 1;
		printf("%s", inet_ntop(AF_INET6, &mp_nlri->nexthop, addr, sizeof(addr)));
		if(len == 32)
		    printf(" %s", inet_ntop(AF_INET6, &mp_nlri->nexthop_local, addr, sizeof(addr)));
	    }
#endif

	    printf(have_nexthop ? "\n" : "N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_MULTI_EXIT_DISC) ) !=0)	printf("   MED          : %d\n",attr->med);
	    else printf("   MED          : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_LOCAL_PREF) ) !=0)		printf("   LOCAL_PREF   : %d\n",attr->local_pref);
	    else printf("   LOCAL_PREF   : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_ATOMIC_AGGREGATE) ) !=0)	printf("   ATOMIC_AGREG : Present\n");
	    else printf("   ATOMIC_AGREG : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_AGGREGATOR) ) !=0)		printf("   AGGREGATOR   : %s AS%u\n",inet_ntoa(attr->aggregator_addr),attr->aggregator_as);
	    else printf("   AGGREGATOR   : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_COMMUNITIES) ) !=0)	printf("   COMMUNITIES  : %s\n",attr->community->str);
	    else printf("   COMMUNITIES  : N/A\n");

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_NEW_AS_PATH) ) !=0) {
		printf("   NEW_ASPATH   : %s\n",attr->new_aspath->str);
	    	printf("   OLD_ASPATH   : %s\n",attr->old_aspath->str);
	    }

	    if( (attr->flag & ATTR_FLAG_BIT(BGP_ATTR_NEW_AGGREGATOR) ) !=0)	printf("   NEW_AGGREGTR : %s AS%u\n",inet_ntoa(attr->new_aggregator_addr),attr->new_aggregator_as);
    }
}

void show_prefixes(int count,struct prefix *prefix) {
    int i;
    for(i=0;i<count;i++)
	printf("      %s/%d\n",inet_ntoa(prefix[i].address.v4_addr),prefix[i].len);
}

#ifdef BGPDUMP_HAVE_IPV6
void show_v6_prefixes(int count, struct prefix *prefix) {
    int i;
    char str[INET6_ADDRSTRLEN];

    for(i=0;i<count;i++){
	inet_ntop(AF_INET6, &prefix[i].address.v6_addr, str, sizeof(str));
	printf("      %s/%d\n",str, prefix[i].len);
    }
}
#endif
