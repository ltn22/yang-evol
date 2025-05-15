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

SCHC imposes that both ends share exactly the same SoR, therefore, a new or modified rule cannot be used while it remains in candidate status until the other end has validated the modification.
A candidate rule cannot be used, either in C/D or F/R. A SCHC PDU MUST NOT be generated with a candidate rule ID and received PDUs containing a candidate rule ID must be dropped.

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

The guard period is used to avoid SCHC message with a rule ID to appear at the other end after a rule modification. The Guard period appears only once during the rule management and is depends on the out-of-sequence messages expected between both ends.

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

# Management messages

## YANG Data Model
CORECONF proposes an interface to manage data structured with a YANG Data Model. RFC 9363 defines a YANG Data Model for SCHC Rules. 
SCHC Instance Management MUST use FETCH to read a rule and iPATCH to create, modify or delete a rule.
In order to accomplish management, the YANG Data Model has been updated. 

### Feature management
M Rules have to be marked in a way that allows quickly identifying which rules in a SoR are responsible for management. 
Therefore, a new feature named "management" has been defined, which characterizes a new "nature-management" type.
This nature is actually a specialization of "nature-compression" for management purposes.

### Guard
To determine if a rule is considered available or not during the guard period, a rule needs to have a status which determines if it can be used. Basically, an available rule MUST associate the key "rule-status" with the value "status-active".
Conversely, during the guard period, "rule-status" MUST be set to "status-candidate".

### YANG tree representation
The YANG tree represents the Rule structure as defined in RFC 9363 with the two updates described above:

~~~
module: ietf-schc
  +--rw schc
     +--rw rule* [rule-id-value rule-id-length]
        +--rw rule-id-value                   uint32
        +--rw rule-id-length                  uint8
        +--rw rule-status                     status-type
        +--rw rule-nature                     nature-type
        +--rw (nature)?
           +--:(fragmentation) {fragmentation}?
           |  +--rw fragmentation-mode        schc:fragmentation-mode-type
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
           +--:(compression) {compression or management}?
              +--rw entry* [field-id field-position direction-indicator]
                 +--rw field-id                    schc:fid-type
                 +--rw field-length                union
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
{: #Fig-tree title='Updated YANG Data Model for CORECONF'}


## Set of Rules Editing
For clarity reasons, this document will use YANG Identifiers in quotes instead of the SID values.
In the YANG tree, all the lines of the tree have a SID number. Each level of the hierarchy is accessible through one or several keys. For example, to access the hierarchy under "rule", "rule-id-value" and "rule-id-length" must be specified. To access the hierarchy describing an entry in a compression rule, "rule-id-value" and "rule-id-length" must be followed by "field-id", "field-position" and "direction-indicator". Since the TV, MO-value and CDA-value are stored as lists, "index" must be added to access a specific element.

Therefore, to access a specific element in a hierarchy, the SID of this element has to be specified, followed by the keys needed to access it.

For example, ["target-value/value", 5, 3, "fid-ipv6-version", 1, "di-bidirectional", 0] is used to access the first value (0) of TV for the IPv6 Version of Rule 5/3.

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
  {"target-value"       : [{"index" : 0, "value" : h"06"}]},
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

The same principle is applied to rules and "leaf-list".

#### Add
If the target object doesn't exist in the context, then it is appended. 
It supports three main cases:
* Adding a new key-value pair to an existing object
* Adding a new object to an existing list

One important specification is that for every leaf-list, the YANG Data Model describes that every index should be incremental. In CORECONF, we trust the user/system.

Example:
- Add TV into fid-ipv6-payload-length/1/di-bidirectional in Rule 0/3
  ~~~
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  {
  ["target-value", 0, 3, "fid-ipv6-payload-length", 1, "di-bidirectional"] : [
      {delta_index : 0, delta_value : h"50"},
      {delta_index : 1, delta_value : h"55"}
  ]
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

Example:
- Delete Rule 7/8
  ~~~
  REQ: iPATCH /c
       (Content-Format: application/yang-identifiers+cbor-seq)
  {
    ["rule", 7, 8]: null
  }
  
  RES: 2.04 Changed
  ~~~

For deletion, we limit the actions and consider a minimal CORECONF representation as {"ietf-schc:schc" : {"rule" : []}}. 
Therefore, a request trying to delete "ietf-schc:schc" will set the CORECONF representation to the minimal one.
Additionally, while updates are authorized, deleting a protected key is forbidden.

Example:
- Delete rule-id-value of Rule 0/3
  ~~~
  REQ: iPATCH /c
       (Content-Format: application/yang-identifiers+cbor-seq)
  {
    ["rule-id-value", 0, 3]: null
  }
  
  RES: 4.00 Bad Request
  ~~~


### Optimization

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

~~~
REQ: FETCH </c>
        (Content-Format: application/yang-identifiers+cbor-seq)
   ["schc-opt:matching-operator", 8, 3, "schc-opt:space-id-CoAP", 11, 1, "di-up"]
~~~

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

The end-point acting as a Device has the IPv6 address fe80::1/64 and the other end fe80::2/64. 

Both implements CoAP client and server capabilities. The server uses port 5683 and the client 3865. 

## Compression Rules

Two rules are required for management functionality. The first rule (RuleID 0) defines packets containing application payloads that include a CoAP Content-Format field. Depending on the direction (Up or Down), this rule manages Confirmable FETCH/iPATCH requests or Non-Confirmable Content responses accordingly. Therefore, the second rule (RuleID 1) is used to compress packets which do not include application payload, basically response packets in downlink.

~~~
 +---------------------------------------------------------------------------------------------+
 |RuleID 0                                                                                     |
 +-------------------+--+--+--+-------------------------------------+-------------+------------+
 |        FID        |FL|FP|DI|                  TV                 |     MO      |    CDA     |
 +-------------------+--+--+--+-------------------------------------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6                                    |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1                                    |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470                               |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|                                     |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17                                   |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64                                   |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64                            |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2                                  |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64                            |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1                                  |equal        |not-sent    |
 +===================+==+==+==+=====================================+=============+============+
 |UDP DevPort        |16|1 |Bi|3865                                 |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683                                 |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|                                     |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|                                     |ignore       |compute-*   |
 +===================+==+==+==+=====================================+=============+============+
 |CoAP Version       |2 |1 |Bi|1                                    |equal        |not-sent    |
 |CoAP Type          |2 |1 |Dw|2                                    |equal        |not-sent    |
 |CoAP Type          |2 |1 |Up|0                                    |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0                                    |equal        |not-sent    |
 |CoAP Code          |8 |1 |Up|[5, 7]                               |match-mapping|mapping-sent|
 |CoAP Code          |8 |1 |Dw|69                                   |equal        |not-sent    |
 |CoAP MID           |16|1 |Bi|0                                    |MSB(9)       |LSB         |
 |CoAP Uri-Path      |8 |1 |Bi|c                                    |equal        |not-sent    |
 |CoAP Content-Format|8 |1 |Bi|application/yang-identifiers+cbor-seq|equal        |not-sent    |
 +===================+==+==+==+=====================================+=============+============+
~~~
{: #Fig-Management-Rule title='Management Rule 0'}

~~~
 +---------------------------------------------------------------------------------------------+
 |RuleID 1                                                                                     |
 +-------------------+--+--+--+-------------------------------------+-------------+------------+
 |        FID        |FL|FP|DI|                  TV                 |     MO      |    CDA     |
 +-------------------+--+--+--+-------------------------------------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6                                    |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1                                    |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470                               |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|                                     |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17                                   |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64                                   |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64                            |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2                                  |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64                            |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1                                  |equal        |not-sent    |
 +===================+==+==+==+=====================================+=============+============+
 |UDP DevPort        |16|1 |Bi|3865                                 |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683                                 |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|                                     |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|                                     |ignore       |compute-*   |
 +===================+==+==+==+=====================================+=============+============+
 |CoAP Version       |2 |1 |Bi|1                                    |equal        |not-sent    |
 |CoAP Type          |2 |1 |Dw|2                                    |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0                                    |equal        |not-sent    |
 |CoAP Code          |8 |1 |Dw|[68, 128, 132]                       |match-mapping|mapping-sent|
 |CoAP MID           |16|1 |Bi|0                                    |MSB(9)       |LSB         |
 +===================+==+==+==+=====================================+=============+============+
~~~
{: #Fig-Management-Rule title='Management Rule 1'}

# OSCORE

## Compression Rules

# DTLS

## Compression Rules


# Example CORECONF Usage in Python

~~~
from typing import Dict, Generator, Tuple
from copy import deepcopy

import pytest

from src.coreconf.coreconf_manager import CORECONFManager
from src.coreconf.coreconf_matching import CORECONFMatchingData


@pytest.fixture
def test_context() -> Generator[Tuple[CORECONFManager, Dict], None, None]:
    """
    Initialize CORECONFManager with test data and provide original context for comparison.

    Returns:
        (Generator[Tuple[CORECONFManager, Dict]]): Manager and original context
    """

    sid_file: str = "./data/yang/ietf-schc@2025-04-16.sid"
    model_file: str = "./data/yang/description.json"
    context_file: str = "./data/context/test.json"

    cc_manager: CORECONFManager = CORECONFManager(
        sid_filename=sid_file,
        yang_model_description_filename=model_file,
        context_filename=context_file,
    )

    # Store original context for comparison without modifying the cc_manager
    original_context: Dict = deepcopy(cc_manager.coreconf_context)

    yield cc_manager, original_context

    # Cleanup
    cc_manager.cancel_pending_timers()

# ********************************************************************** #

def perform_modification(cc_manager: CORECONFManager, yang_request: Dict):
    """Helper to perform modification operation."""

    matching: CORECONFMatchingData = cc_manager.prepare_ipatch_management_request(
        sid_request_args=cc_manager.format_clear_request(request_args=yang_request)
    )[0]

    cc_manager.modify_object(matching_data=matching)

# ********************************************************************** #

def verify_context_equals(cc_manager: CORECONFManager, expected_context: Dict):
    """Assert the context matches expected value."""

    assert cc_manager.check_coreconf_context_equivalence(
        other_coreconf_context=expected_context
    )

# ********************************************************************** #

def verify_context_unchanged(cc_manager: CORECONFManager, original_context: Dict):
    """Assert the context remains unchanged."""

    verify_context_equals(cc_manager=cc_manager, expected_context=original_context)

# =========================== DELETION TESTS =========================== #

def test_delete_root_element(test_context):
    """
    Test deletion of the root element.

    When the root element is deleted, all SCHC rules should be removed,
    but not the entire structure whose minimal structure is {5100: {1: []}}.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc"): None
    }

    expected_result: Dict = {5100: {1: []}}

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_rule(test_context):
    """
    Test deletion of a specific rule.

    When deleting rule 0/3, that specific rule should be removed from the
    configuration while all other rules remain intact.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule", 0, 3): None
    }

    expected_result: Dict = {5100: {1: [{33: 3, 34: 2, 35: 5091, 36: 5094}]}}

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_existing_entry(test_context):
    """
    Test deletion of a specific entry from a rule.

    When deleting the IPv6 Version entry from rule 0/3, the entry should be removed
    while all other entries in the rule remain intact.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry", 0, 3, "fid-ipv6-version", 1, "di-bidirectional"): None
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_on_basic_key(test_context):
    """
    Test deletion of a basic key from a rule.

    When deleting the rule-status field from rule 0/3, that attribute
    should be removed while all other attributes of the rule remain intact.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/rule-status", 0, 3): None
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_leaf_list_single(test_context):
    """
    Test deletion of a single value from a leaf-list.

    When deleting a specific target value (index 0) from the IPv6 Version entry,
    as there is only this value in this structure, the entire key:value is removed.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry/target-value/value", 0, 3, "fid-ipv6-version", 1, "di-bidirectional", 0): None
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_leaf_list_several(test_context):
    """
    Test deletion of a value from a multi-value leaf-list.

    When deleting the second value (index 1) from the traffic class entry,
    only that specific value should be removed, with other values preserved,
    even if indexes become non-incremental.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry/target-value/value", 0, 3, "fid-ipv6-trafficclass", 1, "di-bidirectional", 1): None
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_delete_unknown_entry(test_context):
    """
    Test deletion of a non-existent entry.

    When attempting to delete an entry that doesn't exist (fid-ipv6-version in rule 2/3),
    the context should remain unchanged as there's nothing to delete.
    """

    cc_manager: CORECONFManager
    original_context: Dict
    cc_manager, original_context = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry", 2, 3, "fid-ipv6-version", 1, "di-bidirectional"): None
    }

    perform_modification(cc_manager, yang_request)
    verify_context_unchanged(cc_manager, original_context)

# ********************************************************************** #

def test_delete_protected_key(test_context):
    """
    Test deletion of a protected key.

    When attempting to delete a protected key (rule-id-value), the operation
    should fail and the context should remain unchanged.
    """
    cc_manager: CORECONFManager
    original_context: Dict
    cc_manager, original_context = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/rule-id-value", 0, 3): None
    }

    perform_modification(cc_manager, yang_request)
    verify_context_unchanged(cc_manager, original_context)

# ======================= UPDATE TESTS =======================

def test_update_protected_key(test_context):
    """
    Test updating a protected key.

    When updating a protected key (rule-id-value), the operation should succeed
    and the value should be changed according to the request.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/rule-id-value", 0, 3): 5
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 5, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_update_basic_key(test_context):
    """
    Test updating a basic key.

    When updating a basic key (rule-status), the value should be changed
    according to the request. This tests changing from "active" to "candidate" status.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/rule-status", 0, 3): "status-candidate"
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5096
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ======================= ADDITION TESTS =======================

def test_add_new_entry(test_context):
    """
    Test adding a new entry to a rule.

    When adding a new IPv6 App Prefix entry to rule 0/3,
    the entry should be properly added.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry", 0, 3, "fid-ipv6-appprefix", 1, "di-bidirectional"): {
            "field-length": 64,
            "target-value": [
                {"index": 0, "value": "/oAAAAAAAAA="} # b"\xfe\x80\x00\x00\x00\x00\x00\x00"
            ],
            "matching-operator": "ietf-schc:mo-equal",
            "comp-decomp-action": "ietf-schc:cda-not-sent"
        }
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]},
                        {1: 5015, 5: 5018, 6: 5057, 7: 64, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\xfe\x80\x00\x00\x00\x00\x00\x00"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_add_leaf_list_incremental(test_context):
    """
    Test adding a new value to a leaf-list with incremental index.

    When adding a new value with index 4 to the IPv6 Flow Label entry,
    the value should be properly added.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry/target-value", 0, 3, "fid-ipv6-flowlabel", 1, "di-bidirectional"): {
            "index": 4, "value": "vLw="
        }
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"},
                                {1: 4, 2: b"\xbc\xbc"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_add_leaf_list_non_incremental(test_context):
    """
    Test adding a new value to a leaf-list with non-incremental index.

    When adding a new value with index 7 (skipping indices 4-6) to the IPv6 Flow Label entry,
    the value should be properly added even if it is not maintaining the right order.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry/target-value", 0, 3, "fid-ipv6-flowlabel", 1, "di-bidirectional"): {
            "index": 7, "value": "vLw="
        }
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        { 
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}, 
                                {1: 7, 2: b"\xbc\xbc"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ], 
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_add_new_key_value(test_context):
    """
    Test adding new key-value pair to an existing entry.

    When adding target values to the IPv6 Payload Length entry,
    the values should be properly added with the appropriate structure.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry/target-value", 0, 3, "fid-ipv6-payload-length", 1, "di-bidirectional"): [
            {"index": 0, "value": "UA=="}, 
            {"index": 1, "value": "VQ=="}
        ]
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"}
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"}
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084, 13: [{1: 0, 2: b"\x50"}, {1: 1, 2: b"\x55"}]},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ],
                    33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

def test_add_new_rule(test_context):
    """
    Test adding a completely new rule.

    When adding a new rule (5/3), the rule should be properly added
    with the right (value/length) even is something different is defined.
    """

    cc_manager: CORECONFManager
    cc_manager, _ = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule", 5, 3): {
            "rule-status": "ietf-schc:status-active",
            "rule-id-value": 10,  # difference here
            "rule-id-length": 5,  # difference here
            "rule-nature": "ietf-schc:nature-compression",
        }
    }

    expected_result: Dict = {
        5100: {
            1: [
                {
                    4: [
                        {1: 5015, 5: 5018, 6: 5068, 7: 4, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x06"}]},
                        {
                            1: 5014, 5: 5018, 6: 5065, 7: 8, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\xff"},
                                {1: 1, 2: b"\xfe"},
                                {1: 2, 2: b"\xf1"},
                                {1: 3, 2: b"\xf7"},
                            ]
                        },
                        {
                            1: 5014, 5: 5018, 6: 5061, 7: 20, 8: 1, 9: 5085,
                            13: [
                                {1: 0, 2: b"\x00\xef\x2d"},
                                {1: 1, 2: b"\x0f\xfe\x2d"},
                                {1: 2, 2: b"\x07\x77\x77"},
                                {1: 3, 2: b"\x0f\xf8\x5f"},
                            ]
                        },
                        {1: 5011, 5: 5018, 6: 5064, 7: 16, 8: 1, 9: 5084},
                        {1: 5015, 5: 5018, 6: 5063, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x11"}]},
                        {1: 5015, 5: 5018, 6: 5062, 7: 8, 8: 1, 9: 5083, 13: [{1: 0, 2: b"\x40"}]}
                    ], 33: 3, 34: 0, 35: 5088, 36: 5094
                },
                {33: 3, 34: 2, 35: 5091, 36: 5094},
                {33: 3, 34: 5, 35: 5088, 36: 5094}
            ]
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_equals(cc_manager, expected_result)

# ********************************************************************** #

  def test_add_entry_into_unknown_rule(test_context):
    """
    Test adding an entry into unknown rule.

    When adding a new object into unknown object, the result should
    remain unchanged because other fields, which are not keys, cannot
    be deducted at every depth of the context.
    """

    cc_manager: CORECONFManager
    original_context: Dict
    cc_manager, original_context = test_context

    yang_request: Dict = {
        ("/ietf-schc:schc/rule/entry", 250, 8, "fid-ipv6-payload-length", 1, "di-bidirectional"): {
            "field-length": 16,
            "matching-operator": "ietf-schc:mo-ignore",
            "comp-decomp-action": "ietf-schc:cda-value-sent",
        }
    }

    perform_modification(cc_manager, yang_request)
    verify_context_unchanged(cc_manager, original_context)
~~~



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
