---
v: 3

title: CORECONF Rule management for SCHC
abbrev: SCHC for CoAP
docname: draft-toutain-schc-coreconf-management

v3xml2rfc:
  silence:
  - Found SVG with width or height specified

area: Internet
wg: SCHC Working Group
kw: Internet-Draft
cat: std
submissiontype: IETF

coding: utf-8

author:
      - name: Ana Minaburo
        org: Consultant
        street: Rue de Rennes
        city: Cesson-Sevigne
        code: 35510
        country: France
        email: anaminaburo@gmail.com
      - name: Laurent Toutain
        org: IMT Atlantique
        street: CS 17607, 2 rue de la Chataigneraie
        city: Cesson-Sevigne Cedex
        code: 35576
        country: France
        email: Laurent.Toutain@imt-atlantique.fr
      - name: Corentin Banier
        org: IMT Atlantique
        street: CS 17607, 2 rue de la Chataigneraie
        city: Cesson-Sevigne Cedex
        code: 35576
        country: France
        email: corentin.banier@imt-atlantique.fr

normative:
  RFC8724:
  RFC9363:
  RFC9254:
  I-D.ietf-core-comi:
  I-D.ietf-lpwan-architecture:
  I-D.toutain-schc-universal-option:
  I-D.toutain-schc-sid-allocation:
informative:

entity:
  SELF: "[RFC-XXXX]"

--- abstract

This document describe how CORECONF management can be applied to SCHC Context. 


--- middle

# Introduction{#intro}

{{RFC9363}} defines the YANG Data Model for a SCHC context (a.k.a Set of Rules). {{I-D.ietf-lpwan-architecture}} proposes the architecture for rule management. Some rules must be clearly dedicated to the modification of the context.

{{RFC9254}} defines a way to serialize data issued from a YANG DM into a CBOR representation and {{I-D.ietf-core-comi}} defines the CoAP interface.

This document describes in which condition management can be done, how to manage rules inside an SCHC instance using CORECONF and proposes some compression rules for the protocol headers.

# Applicability statement

## Architecture

SCHC instance management allows the two end-points to modify the common SoR, by:

* modifyng rules values (such as TV, MO or CDA) in existing rules
* adding a new rule or 
* removing an existing rules. 

The rule management uses the CORECONF interface {{I-D.ietf-core-comi}} based on CoAP. The management traffic is carried as SCHC compressed packets tagged to some specific rule IDs. They are identified as M rules in Figure {{Fig-SCHCManagement}}.  M Rules can be either Compression rules or No compression rules. Only M rules can modify the SoR.


SCHC Packets using M Rules MUST be encrypted either by the underlying layer (for instance in a QUIC stream dedicated to managenement inside a QUIC connection) or directly using OSCORE of DTLS.

~~~~ aasvg
+-----------------+                 +-----------------+
|       ^         |                 |       ^         |
|  C/D  !  M ___  |                 |       !  M ___  |
|       +-->[SoR] |       ...       |       +-->[SoR] |
|       !   [___] |                 |       !   [___] |
|       !         |                 |       !         |
|      F/R        |                 |      F/R        |
+------ins_id1----+-----ins_idi-----+------ins_idn----+         
.                   C/D  !                       ___  .
.                        +--------------------->[SoR] .    
.                       F/R               M     [___] .
+.................. Discriminator ....................+
~~~~
{: #Fig-SCHCManagement title='Inband Management'}

## CoAP Profile

Management requests MUST be protected against packet losts. It is RECOMMENDED to use CONfirmable requests and no Token. If the management request is too large regarding the MTU, SCHC Fragmentation SHOULD be used instead of the Block option.

## Rule modification

SCHC imposes both ends to share exactly the same SoR, therefore, a new or modified rule could be used, until the rule remains candidate until the other end has validated the modification. 
A canditate rule cannot be used, either in C/D or F/R. A SCHC PDU MUST not be generated with a candidate rule ID and received PDU containing 
a candidate rule must be dropped.  

~~~ aasvg
              A                         X  B
 X valid      |     modify Rule x    ------| X valid
 X candidate  |=====================/=====>| X candidate
              |        /------------       |
           ---|<======/====================|----
            | |      /                     |  |
     Guard  | |<-----                      |  | Guard
            v |                            |  v
           ---|                            |----   
 X valid      |                            | X valid

~~~
{: #Fig-Rule-mod title='Modifying a rule'}


{{Fig-Rule-mod}} illustrates a Rule modification. The left-hand side entity A wants to make rule x evolve.  It send and acknowledged CoAP message to the other end. 
A change the status of the rule to candidate, indicating that the rule cannot be used anymore for SCHC procedures. The receiving entity B, acknowledge the message,
and contiue to maintain the rule candidate for a guard period. At the reception of the acknowledgement, A set also a guard period before rule x becomes valid again.

The guard period is used to avoid SCHC message with a rule ID to appear at the other end after a rule modification. The Guard period appears only once during the
rule management and is depends on the out-of-sequence messages expected between both ends.

## Rule creation 

Rule creation do not require a guard period, and acknowledgment is RECOMMENDED. Figure {{Fig-Rule-creation}} gives an example, where the Acknowledgment is lost.
Entity A sends a management message to create a new rule. Since its a new rule, the guard period is not set and the new rule becomes immediatly valid on B. 
The Acknowledgement does not reach back A, so the rule stays in the candidate state, but the reception of a SCHC PDU carrying the RulE ID X, informs that the
message has been correctly received by B. So X becomes valid in A. 


~~~ aasvg
              A                            B
 X created    |       
 X candidate  |===========================>| X valid
              |         X==================|
              |                            |   
   X valid    |<---------------------------|   
              |               X            | 
              |                            | 

~~~
{: #Fig-Rule-creation title='Modifying a rule'}

## Rule deletion

After the rule deletion, a Guard period is established. During that period, a rule with the same ID cannot be created, and SCHC PDU corrying the Rule ID are dropped.

# Management messages.

## Set of Rules Editing

CORECONF proposes an interface to manage data structured with a YANG Data Model. RFC 9363 defines a YANG Data Model for SCHC Rules. 
SCHC Instance Management MUST use a FETCH to read a rule and iPATCH to create, modify or delete a rule.

For clarity reasons, the document will use YANG Identifier in quote instead of the SID value.

The YANG tree represents the Rule structure as defined in RFC 9363:

~~~

module: ietf-schc
     +--rw schc
        +--rw rule* [rule-id-value rule-id-length]
           +--rw rule-id-value                   uint32
           +--rw rule-id-length                  uint8
           +--rw rule-nature                     nature-type
           +--rw (nature)?
              +--:(fragmentation) {fragmentation}?
              |  +--rw fragmentation-mode
              |  |       schc:fragmentation-mode-type
              |  +--rw l2-word-size?             uint8
              |  +--rw direction                 schc:di-type
              |  +--rw dtag-size?                uint8
              |  +--rw w-size?                   uint8
              |  +--rw fcn-size                  uint8
              |  +--rw rcs-algorithm?            rcs-algorithm-type
              |  +--rw maximum-packet-size?      uint16
              |  +--rw window-size?              uint16
              |  +--rw max-interleaved-frames?   uint8
              |  +--rw inactivity-timer
              |  |  +--rw ticks-duration?   uint8
              |  |  +--rw ticks-numbers?    uint16
              |  +--rw retransmission-timer
              |  |  +--rw ticks-duration?   uint8
              |  |  +--rw ticks-numbers?    uint16
              |  +--rw max-ack-requests?         uint8
              |  +--rw (mode)?
              |     +--:(no-ack)
              |     +--:(ack-always)
              |     +--:(ack-on-error)
              |        +--rw tile-size?          uint8
              |        +--rw tile-in-all-1?      schc:all-1-data-type
              |        +--rw ack-behavior?       schc:ack-behavior-type
              +--:(compression) {compression}?
                 +--rw entry*
                         [field-id field-position direction-indicator]
                    +--rw field-id                    schc:fid-type
                    +--rw field-length                schc:fl-type
                    +--rw field-position              uint8
                    +--rw direction-indicator         schc:di-type
                    +--rw target-value* [index]
                    |  +--rw index    uint16
                    |  +--rw value?   binary
                    +--rw matching-operator           schc:mo-type
                    +--rw matching-operator-value* [index]
                    |  +--rw index    uint16
                    |  +--rw value?   binary
                    +--rw comp-decomp-action          schc:cda-type
                    +--rw comp-decomp-action-value* [index]
                       +--rw index    uint16
                       +--rw value?   binary
~~~
{: #Fig-tree title='Modifying a rule'}

Almost all the lines of the tree as a SID number. Each level of the hierarchy is accessible through one or several keys. For example, to access the hierarchy under "rule", "rule-id-value" and "rule-id-length" must be specified. To access the hierarchy describing an entry in a compression rule, "rule-id-value" and "rule-id-length" followed by "field-id", "field-position" and "direction-indicator". Since the TV, MO-value and CDA-value are stored as list, "index" must be added to access a specific element.

Therefore to access a specific element in a hierarchy, the SID of this element has to be specified, followed by the keys needed to access it. 

For example, ["target-value/value", 5, 3, "fid-ipv6-version", 1, "di-bidirectional", 0] is used to access to the first value (0) of TV for the IPv6 Version of Rule 5/3. 

### FETCH
As mentionned in {{I-D.ietf-core-comi}}, FETCH request helps to retrieve at least one instance-value.

Example : Fetching TV, MO and CDA of the Entry fid-ipv6-version/1/bidirectional from Rule 6/3.
~~~
REQ: FETCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
["target-value",       6, 3, "fid-ipv6-version", 1, "di-bidirectional"],
["matching-operator",  6, 3, "fid-ipv6-version", 1, "di-bidirectional"],
["comp-decomp-action", 6, 3, "fid-ipv6-version", 1, "di-bidirectional"]

RES: 2.05 Content
     (Content-Format: application/yang-instances+cbor-seq)
{
  {"target-value"       : [{"index" : 0, "value" : "Bg=="}]},
  {"matching-operator"  : "mo-equal"},
  {"comp-decomp-action" : "cda-not-sent"}
}
~~~

### iPATCH

To write an iPATCH request, several methods could be used. For instance, in a Rule 7/8, an entry for a field was set to ignore/value-sent and the target-value was not set, these following commands specify a new TV and change the MO and CDA :
- Specified all conserned fields :
  ~~~
  iPATCH /c 
  {
    ["target-value", 7, 8, field, 1, "di-bidirectional"] : [{delta_TV: 0, delta_value: value}],
    ["matching-operator", 7, 8, field, 1, "bi-directional"] : "mo-equal",
    ["comp-decomp-action", 7, 8, field, 1, "bi-directional"] : "cda-not-sent"
  }
  ~~~

- This can also be specified in a single entry, by setting the sub-tree:
  ~~~
  iPATCH /c 
  {
    ["entry", 7, 8, field, 1, "di-bidirectional"] : { 
        delta_target-value       : [{delta_index : 0, delta_value : value}],
        delta_matching-operator  : "mo-equal",
        delta_comp-decomp-action : "cda-not-sent"
    }
  }
  ~~~

The same principle is applied to rules and "leaf-list". However, each index of "leaf-list" might be in a row. Therefore, manipulating these values should be checked.


#### Add

If the target object doesn't exist in the context, then it is appended. As if the request is adding looking to add a leaf-list item, a cheching is processed. For instance, if ["target-value", 6, 3, "fid-ipv6-flowlabel", 1, "di-bidirectional"] corresponds to [{"index" : 0, "value" : "AO8t"}]. The following request might return an error.
~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["target-value", 6, 3, "fid-ipv6-flowlabel", 1, "di-bidirectional"] : {
      {delta_index : 3, delta_value : "D/4t"}
  }
}

RES: 4.00 Bad Request
~~~

Here is correct request :
~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["target-value", 6, 3, "fid-ipv6-flowlabel", 1, "di-bidirectional"] : {
      {delta_index : 1, delta_value : "D/4t"}
  }
}

RES: 2.04 Changed
~~~

#### Update

A request can be considered as an update if the target associated with the various keys is present in the context. Otherwise, it could be consider as an add or an error.

Example : 
- The Entry fid-ipv6-version/1/di-bidirectional is in Rule 6/3.
~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["entry", 6, 3, "fid-ipv6-version", 1, "di-bidirectional"] : {
      {"delta_target-value"       : []},
      {"delta_matching-operator"  : "mo-ignore"},
      {"delta_comp-decomp-action" : "cda-value-sent"}
  }
}

RES: 2.04 Changed
~~~

- The Entry fid-ipv6-version/1/di-bidirectional is in not in Rule 7/8 but Rule 7/8 exist.
~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["entry", 7, 8, "fid-ipv6-version", 1, "di-bidirectional"] : {
      {"delta_target-value"       : []},
      {"delta_matching-operator"  : "mo-ignore"},
      {"delta_comp-decomp-action" : "cda-value-sent"}
  }
}

RES: 2.04 Changed
~~~

- The Entry fid-ipv6-version/1/di-bidirectional is not in Rule 5/8, and Rule 5/8 does not exist. Therefore, Rule 5/8 cannot be added in order to include the Entry fid-ipv6-version/1/di-bidirectional because other fields, which are not keys, cannot be deducted at every depth of the context.
~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["entry", 5, 8, "fid-ipv6-version", 1, "di-bidirectional"] : {
      {"delta_target-value"       : []},
      {"delta_matching-operator"  : "mo-ignore"},
      {"delta_comp-decomp-action" : "cda-value-sent"}
  }
}

RES: 4.04 Not Found
~~~

#### Delete
To remove an object we use "null" value.

~~~
REQ: iPATCH /c
     (Content-Format: application/yang-identifiers+cbor-seq)
{
  ["rule", 7, 8]: null
}

RES: 2.04 Changed
~~~

This process imposes to send the full rule in the value part, so an optimization can be done by deriving an exisiting rule and modify some parameters. 

{{I-D.toutain-schc-universal-option}} augments the data model for universal options. This add to compression rules a new entry format where a field is indexed with:

* a space-id, a YANG identifier refering to the protocol containing options (CoAP, QUIC, TCP,...)
* the option used in the protocol
* the position 


~~~ 
  +--rw schc-opt:entry-option-space* \
      [space-id option-value field-position direction-indicator]
     +--rw schc-opt:space-id                    space-type
     +--rw schc-opt:option-value                uint32
     +--rw schc-opt:field-length                union
     +--rw schc-opt:field-position              uint8
     +--rw schc-opt:direction-indicator         schc:di-type
     +--rw schc-opt:target-value* [index]
     |  +--rw schc-opt:index    uint16
     |  +--rw schc-opt:value?   binary
     +--rw schc-opt:matching-operator           schc:mo-type
     +--rw schc-opt:matching-operator-value* [index]
     |  +--rw schc-opt:index    uint16
     |  +--rw schc-opt:value?   binary
     +--rw schc-opt:comp-decomp-action          schc:cda-type
     +--rw schc-opt:comp-decomp-action-value* [index]
        +--rw schc-opt:index    uint16
        +--rw schc-opt:value?   binary
~~~

In the CORECONF representation, even if the name are similar in the structure, the SID values are different. The key contains for an entry contains 4 elements.

~~~~
REQ: FETCH </c>
        (Content-Format: application/yang-identifiers+cbor-seq)
   ["schc-opt:matching-operator", 8, 3, "schc-opt:space-id-coap", 11, 1, "di-up"]
~~~~~

## RPC

Represented as a tree:

~~~
  rpcs:
    +---x duplicate-rule
       +---w input
       |  +---w from
       |  |  +---w rule-id-value?    uint32
       |  |  +---w rule-id-length?   uint8
       |  +---w to
       |     +---w rule-id-value?    uint32
       |     +---w rule-id-length?   uint8
       +--ro output
          +--ro status?   string
~~~~


After duplication, the new rule stays in a candidate state until the new values are set. 

# Protocol Stack

The management inside the instance has its own IPv6 stack totally independant of the rest of the system. The goal is to implement IPv6/UDP/CoAP to allow the implementation of the CORECONF interface. No other kind of traffic is allowed.

The end-point acting as a Device has the IPv6 address FE80::1/64 and the other end FE80::2/64. 

Both implements CoAP client and server capabilities. The server uses port 5684 and the client 4865. 

## Compression Rules

# OSCORE

## Compression Rules

# DTLS

## Compression Rules






--- back


# YANG DM


  rpc duplicate-rule {
        input {
          container from {
            uses ietf-schc:rule-id-type;
          }
          container to {
            uses ietf-schc:rule-id-type;
          }
        }
        output {
          leaf status {
            type string;
          }
        }
      }




# Acknowledgments # {#acknowledgments}
{:unnumbered}

The authors sincerely thank

This work was supported by the Sweden's Innovation Agency VINNOVA within the EUREKA CELTIC-NEXT project CYPRESS.
