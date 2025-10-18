---
v: 3

title: CORECONF Rule management for SCHC
abbrev: SCHC for CoAP
docname: draft-toutain-schc-coreconf-management-01
ipr: trust200902

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
      - name: Javier A. Fernandez
        org: IMT Atlantique
        street: CS 17607, 2 rue de la Chataigneraie
        city: Cesson-Sevigne Cedex
        code: 35510
        country: France
        email: javier-alejandro.fernandez@imt-atlantique.fr
      - name: Corentin Banier
        org: IMT Atlantique
        street: CS 17607, 2 rue de la Chataigneraie
        city: Cesson-Sevigne Cedex
        code: 35576
        country: France
        email: corentin.banier@imt-atlantique.fr
      - name: Marion Dumay
        org: Orange
        email: marion.dumay@orange.com


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

This document describes how CORECONF can be applied to SCHC for context and rule set management between endpoints.


--- middle

# Introduction {#intro}

{{RFC9363}} defines the YANG Data Model for a SCHC context (a.k.a Set of Rules, or SoR). {{I-D.ietf-lpwan-architecture}} proposes the architecture for rule management. Some rules must be clearly dedicated to the modification of the context.

{{RFC9254}} defines a way to serialize data issued from a YANG DM into a CBOR representation and {{I-D.ietf-core-comi}} defines the CoAP interface.

This document describes how CORECONF can be used to manage SCHC contexts and rule sets within a SCHC instance. It also specifies SCHC compression rules tailored for the CORECONF-based management traffic itself. These “management compression rules” improve efficiency for control and configuration exchanges, distinct from the compression applied to regular application data.

# Applicability statement

## Architecture

SCHC instance management allows the two endpoints to modify the common SoR, by:

* Modifying rules values (such as TV, MO or CDA) in existing rules.
* Adding a new rule.
* Removing an existing rule.
* Triggering Remote Procedural Calls (RPC) within the endpoints.

A new type of traffic is defined called management traffic, which deals exclusively with message exchanges concerning context and rule management.

The rule management uses the CORECONF network management interface {{I-D.ietf-core-comi}}, which is based on CoAP. In this context, management traffic refers to the CORECONF messages exchanged between the endpoints to configure or modify rule sets. The management traffic is transported as SCHC-compressed packets, tagged with specific Rule IDs. These rules are identified as Management Rules (or M Rules) in Figure {{Fig-SCHCManagement}}. M Rules can be either Compression Rules or No-Compression Rules. Only M Rules are permitted to modify the SoR.

The management traffic uses its own IPv6 stack, distinct from regular application traffic. See Section {{sec-protocols}} for more details.

SCHC Packets using M Rules MUST be encrypted either by the underlying layer (for instance in a QUIC stream dedicated to management inside a QUIC connection) or directly using OSCORE or DTLS.

~~~~ aasvg
+-----------------+                 +-----------------+
|       ^         |                 |       ^         |
|  C/D  !M    ___ |                 |       !M    ___ |
|       +-[]>[SoR]|       ...       |       +-[]>[SoR]|
|       !    [___]|                 |       !    [___]|
|       !         |                 |       !         |
|      F/R        |                 |      F/R        |
+------ins_id1----+-----ins_idi-----+------ins_idn----+         
.                   C/D  !    M         +---+    ___  .
.                        +------------->|Mng|<=>[SoR] .    
.                       F/R             +---+   [___] .
+.................. Discriminator ....................+
~~~~
{: #Fig-SCHCManagement title='Inband Management'}

## CoAP Profile

Management requests MUST be protected against packet loss. It is RECOMMENDED to use CONfirmable requests and no Token. If the management request is too large regarding the MTU, SCHC Fragmentation SHOULD be used instead of the Block option. As shown in figure {{Fig-SCHCManagement}} fragmentation can be common to Management rules and other rules.

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


{{Fig-Rule-mod}} illustrates a Rule modification. The left-hand side entity A wants to make rule x evolve.  It send an acknowledged CoAP message to the other end. 
Host A change the status of the rule to "candidate", indicating that the rule can no longer be used for SCHC procedures. The receiving entity B, acknowledges the message
and continues to maintain the "candidate" status for a Guard period. At the reception of the acknowledgement, A set also a Guard period before rule x becomes valid again.

The Guard period is used to avoid SCHC message with a rule ID to appear at the other end after a rule modification. The Guard period appears only once during the rule management and is depends on the out-of-sequence messages expected between both ends.

## Rule creation 

Rule creation do not require a Guard period, and acknowledgement is RECOMMENDED. Figure {{Fig-Rule-creation}} gives an example, where the Acknowledgment is lost.
Entity A sends a management message to create a new rule. Since its a new rule, the Guard period is not set and the new rule becomes immediately valid on B. 
The Acknowledgement does not reach A, so the rule stays in the candidate state, but the reception of a SCHC PDU carrying the RulE ID X, informs that the
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

### Management Rule Nature
M Rules have to be marked in a way that allows quickly identifying which rules in a SoR are responsible for management. 
Therefore, a new "nature-management" type has been defined. This nature is actually a specialization of "nature-compression" for management purposes and compression needs to be available and activated to do management.

### Guard Period
To determine if a rule is considered available or not during the Guard period, a rule needs to have a status which determines if it can be used. Basically, an available rule MUST associate the key "rule-status" with the value "status-active".
Conversely, during the Guard period, "rule-status" MUST be set to "status-candidate".

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
For clarity reasons, this document will use YANG Identifiers in quotes instead of SID values.
Each entry in the YANG tree has a corresponding SID number. Each level of the hierarchy is accessible through one or several keys. For example, to access the hierarchy under "rule", "rule-id-value" and "rule-id-length" must be specified. To access the hierarchy corresponding to a field entry in a compression rule, "rule-id-value" and "rule-id-length" must be followed by "field-id", "field-position" and "direction-indicator". Since the TV, MO-value, and CDA-value are stored as lists, "index" must be added to access a specific element.

Therefore, to access a specific element in a hierarchy, the SID of this element has to be specified, followed by the keys needed to access it.

For example, `["target-value/value", 5, 3, "fid-ipv6-version", 1, "di-bidirectional", 0]` is used to access the first value (0) of TV for the IPv6 Version of Rule 5/3.

## Management Errors

There are different levels of error detection:

* CORECONF Errors: these errors are directly generated at the CORECONF-managed context level. For instance, retrieving a value with a wrong key.
* YANG validation errors: the data model does not conform with constraints such as "must" or "mandatory". This check is optional, since it may require a lot of resources on a device.
* SCHC errors: errors on the Data Model that cannot be detected at the YANG level. For example, the rule numbering does not correspond to a binary tree. 

## CoAP Methods

### FETCH

As mentioned in {{I-D.ietf-core-comi}}, FETCH requests are used to retrieve at least one instance-value.

Example: Fetching TV, MO and CDA of the Entry fid-ipv6-version/1/bidirectional from Rule 6/3.

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

Several payload formats can be used in a CoAP iPATCH request to modify SCHC rule parameters. For example, when a field entry in Rule 7/8 is configured as ignore/value-sent and no target value has been defined, the following iPATCH request payload sets a new Target Value (TV) and updates the corresponding Matching Operator (MO) and Compression/Decompression Action (CDA):

~~~
  iPATCH /c 
  {
    ["target-value", 7, 8, field, 1, "di-bidirectional"] : [{delta_TV: 0, delta_value: value}],
    ["matching-operator", 7, 8, field, 1, "bi-directional"] : "mo-equal",
    ["comp-decomp-action", 7, 8, field, 1, "bi-directional"] : "cda-not-sent"
  }
~~~

It is possible to represent each field update as a separate entry in the payload, as shown above.
However, when the modifications apply to elements of the same subtree, it is RECOMMENDED to group them within a single structure inside the iPATCH request payload, as shown below:

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

Both payload formats are valid encodings for a CoAP iPATCH request. The interpretation and application of the modifications are implementation-specific.

<!--LT: I don't understand-- Alejandro: clear now? -->
The same approach applies to rule updates and YANG leaf-list objects, where multiple related modifications may be grouped within a single iPATCH request.

#### Adding an element

If the target object, field, or entry does not exist in the SCHC context, it is added.
It supports two main cases:

* Adding a new key-value pair to an existing object.
* Adding a new object to an existing list.

When adding a new element to a YANG leaf-list in the SCHC context, the model requires that each list index be strictly incremental. CORECONF does not enforce this automatically; it relies on the client or system to provide correctly ordered indices.

Example: Add TV into fid-ipv6-payload-length/1/di-bidirectional in Rule 0/3

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

#### Modify an element

If the target object, field, or entry does exist in the SCHC context, it is updated.

Examples: 

- The Entry fid-ipv6-version/1/di-bidirectional is in Rule 6/3.

~~~
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  {
    ["entry", 6, 3, "fid-ipv6-version", 1, "di-bidirectional"] : {
        {"delta_target-value": []},
        {"delta_matching-operator": "mo-ignore"},
        {"delta_comp-decomp-action": "cda-value-sent"}
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

#### Delete an element

If the specified value in the request is "null", it deletes an object, field, or entry from the SCHC context

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

When deleting objects in the SCHC context via iPATCH, the operation is restricted to prevent removal of required structural elements. Deleting the top-level object (`ietf-schc:schc`) does not remove it entirely; instead, the object is reset to a minimal representation:

~~~
{"ietf-schc:schc": {"rule": []}}
~~~

This ensures the SCHC context remains structurally valid. Updates to existing objects are generally allowed, but deletion of protected keys is forbidden.

Example: Delete rule-id-value of Rule 0/3

~~~
  REQ: iPATCH /c
       (Content-Format: application/yang-identifiers+cbor-seq)
  {
    ["rule-id-value", 0, 3]: null
  }
  
  RES: 4.00 Bad Request
~~~

### POST {#sec-post-method}

As described in {{I-D.ietf-core-comi}}, the POST CoAP method is used to trigger Remote Procedure Calls (RPC) and other actions within a SCHC endpoint. Thus, a POST message can be sent to invoke a specific RPC on the remote endpoint. Details of the supported RPCs and their behavior are defined in Section {{sec-rpcs}}.

RPCs and actions are defined in a YANG Data Model with optional associated inputs and outputs, 
The request payload contains the RPC input map, if any. The response payload contains the corresponding output map, if any.

### Optimizations

Two optimizations are possible: first, deriving rules to avoid sending the full object; second, using universal option indexing for fine-grained field updates.

#### Derive-from-existing-rule optimization

When sending SCHC rules in iPATCH messages, the naive approach is to include the full rule object in the payload, even if only a few fields need to be updated. This can be inefficient, especially in constrained environments. To reduce the amount of data transmitted, an optimization consists in deriving a new rule from an existing one and specifying only the fields that are changing.

Therefore, for adding new rules, the RECOMMENDED method is to use the `duplicate-rule` RPC, defined in Section {{sec-duplicate-rule-rpc}}, which implements this derivation mechanism efficiently.

#### Universal-options optimization

The data model for universal options {{I-D.toutain-schc-universal-option}} augments SCHC compression rules with a structured format for protocol options. Each entry is indexed by:

* a space-id, referring to the protocol containing the option (e.g., CoAP, QUIC, TCP),
* the option itself, and
* the position of the field within the protocol header.

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

In the CORECONF representation, even though the structural names may resemble each other, the SID values differ.
Each entry key consists of four elements, enabling precise referencing of individual protocol fields and allowing efficient selective field-level updates without touching the rest of the rule.

~~~
REQ: FETCH </c>
        (Content-Format: application/yang-identifiers+cbor-seq)
   ["schc-opt:matching-operator", 8, 3, "schc-opt:space-id-coap", 11, 1, "di-up"]
~~~

## RPC statements {#sec-rpcs}

A YANG "RPC" is an operation that may be invoked within a SCHC endpoint and triggers a specified behavior. Within the context of rule management, RPCs are used to perform actions on the set of rules and may also be used for other operations, such as rebooting the remote device endpoint.

Each RPC resource has specific inputs and outputs, and may be invoked remotely via a POST CoAP message, as described in Section {{sec-post-method}}.


### Duplicate Rule (#sec-duplicate-rule-rpc)

To add a new rule, instead of using the iPATCH method with a full rule definition (especially when the new rule is similar to an existing one), the RECOMMENDED approach is to use the `duplicate-rule` RPC. This operation copies an existing rule ("from") into a new rule ("to"), and can optionally include an iPATCH sequence specifying modifications to apply to the duplicated rule. The output returns a status string conveying the result of the operation.

Represented as a tree:

~~~
  rpcs:
    +---x duplicate-rule
       +---w input
       |  +---w from
       |  |  +---w rule-id-value     uint32
       |  |  +---w rule-id-length    uint8
       |  +---w to
       |  |  +---w rule-id-value     uint32
       |  |  +---w rule-id-length    uint8
       |  +---w ipatch-sequence?   binary
       +--ro output
          +--ro status?   string
~~~~

This mechanism reduces management overhead and addresses the isue of adapting to variable application traffic. For example, a SCHC instance may begin with a generic rule with low compression rate, but progressively make rule duplications to make more specialized rules that better match the observed traffic patterns, acheiving higher compression rates and thus adapting the rule set dynamically to the session characteristics.

To maintain consistent rule indexing and enable efficient rule matching, newly created rules SHOULD follow a binary tree structure. For instance, a rule identified as 8/4 may be duplicated as either 8/5 or 18/5, thereby extending the rule identifier by one bit.

Example:

- Representation with identifiers for clarity. Delta-encoded SIDs are used in a real request.

~~~
REQ:  POST </c>
      (Content-Format: application/yang-instances+cbor-seq)

{
  "/ietf-schc:duplicate-rule":
  {
    "input/from/rule-id-value": 8,
    "input/from/rule-id-length": 4,
    "input/to/rule-id-value": 7,
    "input/to/rule-id-length": 4,
    "input/ipatch-sequence":
      [
        "/ietf-schc:schc/rule/entry/target-value/value", 8, 5,
        "fid-coap-mid", 1, "di-bidirectional", 0,
      ]: "FAA="
  }
}

RES:  2.04 Changed
      (Content-Format: application/yang-instances+cbor-seq)

{
  "/ietf-schc:duplicate-rule":
  {
    "output/status": "success",
  }
}
~~~

#### Error Handling

The `duplicate-rule` operation SHALL be atomic. If an error occurs during either stage of the process (rule duplication or subsequent modification through the iPATCH sequence) the SCHC endpoint MUST revert any partial changes to restore the previous state.
The RPC output MUST indicate the failure, for example with an error status such as `Bad Request`, to signal that the duplication did not take place as requested.
The precise error code and diagnostic message are implementation-dependent but SHOULD provide enough context for the management entity to identify the cause of failure.

# Protocol Stack {#sec-protocols}

The management inside the instance has its own IPv6 stack, independent of the application traffic. IPv6/UDP/CoAP is used to allow the implementation of the CORECONF interface. No other kind of traffic is allowed.

The end-point acting as a Device has the IPv6 address fe80::1/64 and the other end, the Core, is assigned the address fe80::2/64. 

Both endpoints implement CoAP client and server capabilities, that is, both endpoints are capable of sending requests and processing responses. The server uses port 5683 and the client 3865. 

## Management Compression Rules (M Rules)

To enable CORECONF-based context and rule management over SCHC, a set of dedicated management rules, identified as M rules, is defined. These rules are used exclusively for management traffic, that is, packets exchanged between SCHC endpoints for the purpose of managing rules, not for application data transfer.

This specification introduces four rules, allowing bidirectional operation and fine control over management capabilities.
Each rule defines the compression behavior for management messages in its direction, distinguishing between requests and responses.

* M1: Handles packets containing a payload (e.g., CoAP requests or Content responses) in one direction (Uplink).
* M2: Handles packets without a payload (e.g., CoAP responses) in the same direction (Uplink).
* M3: Mirrors M1 in the opposite direction (Downlink), for payload-bearing management messages.
* M4: Mirrors M2 in the opposite direction (Downlink), for payloadless messages.

Implementations MAY choose to support only a subset of these rules, depending on their operational or security requirements. For instance, an implementation may include only M3 and M4 to permit management operations exclusively from one endpoint, effectively preventing unsolicited management requests in the other direction. In this sense, the absence of certain M rules in the SoR implicitly acts as a policy mechanism or safeguard for rule management operations.

M rules are protected elements within the SoR. They define the operation of the management channel itself and therefore MUST NOT be modified, duplicated, or deleted through CORECONF operations. Any attempt to apply a modification or duplication request to an M rule MUST result in an Unauthorized error response. This restriction ensures the integrity and stability of the SCHC management process.

~~~
 +-------------------------------------------------------------------+
 |RuleID M1                                                          |
 +-------------------+--+--+--+-----------+-------------+------------+
 |        FID        |FL|FP|DI|  TV       |     MO      |    CDA     |
 +-------------------+--+--+--+-----------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6          |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1          |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470     |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|           |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17         |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64         |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64  |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2        |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64  |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1        |equal        |not-sent    |
 +===================+==+==+==+===========+=============+============+
 |UDP DevPort        |16|1 |Bi|3865       |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683       |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|           |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|           |ignore       |compute-*   |
 +===================+==+==+==+===========+=============+============+
 |CoAP Version       |2 |1 |Bi|1          |equal        |not-sent    |
 |CoAP Type          |2 |1 |Dw|2          |equal        |not-sent    |
 |CoAP Type          |2 |1 |Up|0          |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0          |equal        |not-sent    |
 |CoAP Code          |8 |1 |Up|[2, 5, 7]  |match-mapping|mapping-sent|
 |CoAP Code          |8 |1 |Dw|69         |equal        |not-sent    |
 |CoAP MID           |16|1 |Bi|0          |MSB(9)       |LSB         |
 |CoAP Uri-Path      |8 |1 |Bi|c          |equal        |not-sent    |
 |CoAP Content-Format|8 |1 |Bi|application|equal        |not-sent    |
 |                   |  |  |  |/yang-ident|             |            |
 |                   |  |  |  |fiers+cbor-|             |            |
 |                   |  |  |  |seq        |             |            |
 +===================+==+==+==+===========+=============+============+
~~~
{: #Fig-M1 title='Management Rule 1'}

~~~
 +----------------------------------------------------------------------+
 |RuleID M2                                                             |
 +-------------------+--+--+--+--------------+-------------+------------+
 |        FID        |FL|FP|DI|      TV      |     MO      |    CDA     |
 +-------------------+--+--+--+--------------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6             |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1             |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470        |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|              |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17            |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64            |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64     |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2           |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64     |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1           |equal        |not-sent    |
 +===================+==+==+==+==============+=============+============+
 |UDP DevPort        |16|1 |Bi|3865          |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683          |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|              |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|              |ignore       |compute-*   |
 +===================+==+==+==+==============+=============+============+
 |CoAP Version       |2 |1 |Bi|1             |equal        |not-sent    |
 |CoAP Type          |2 |1 |Dw|2             |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0             |equal        |not-sent    |
 |CoAP Code          |8 |1 |Dw|[68, 128, 129,|match-mapping|mapping-sent|
 |                   |  |  |  | 132, 160]    |             |            |
 |CoAP MID           |16|1 |Bi|0             |MSB(9)       |LSB         |
 +===================+==+==+==+==============+=============+============+
~~~
{: #Fig-M2 title='Management Rule 2'}

~~~
 +-------------------------------------------------------------------+
 |RuleID M3                                                          |
 +-------------------+--+--+--+-----------+-------------+------------+
 |        FID        |FL|FP|DI|  TV       |     MO      |    CDA     |
 +-------------------+--+--+--+-----------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6          |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1          |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470     |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|           |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17         |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64         |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64  |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2        |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64  |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1        |equal        |not-sent    |
 +===================+==+==+==+===========+=============+============+
 |UDP DevPort        |16|1 |Bi|3865       |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683       |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|           |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|           |ignore       |compute-*   |
 +===================+==+==+==+===========+=============+============+
 |CoAP Version       |2 |1 |Bi|1          |equal        |not-sent    |
 |CoAP Type          |2 |1 |Up|2          |equal        |not-sent    |
 |CoAP Type          |2 |1 |Dw|0          |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0          |equal        |not-sent    |
 |CoAP Code          |8 |1 |Dw|[2, 5, 7]  |match-mapping|mapping-sent|
 |CoAP Code          |8 |1 |Up|69         |equal        |not-sent    |
 |CoAP MID           |16|1 |Bi|0          |MSB(9)       |LSB         |
 |CoAP Uri-Path      |8 |1 |Bi|c          |equal        |not-sent    |
 |CoAP Content-Format|8 |1 |Bi|application|equal        |not-sent    |
 |                   |  |  |  |/yang-ident|             |            |
 |                   |  |  |  |fiers+cbor-|             |            |
 |                   |  |  |  |seq        |             |            |
 +===================+==+==+==+===========+=============+============+
~~~
{: #Fig-M3 title='Management Rule 3'}

~~~
 +----------------------------------------------------------------------+
 |RuleID M4                                                             |
 +-------------------+--+--+--+--------------+-------------+------------+
 |        FID        |FL|FP|DI|      TV      |     MO      |    CDA     |
 +-------------------+--+--+--+--------------+-------------+------------+
 |IPv6 Version       |4 |1 |Bi|6             |equal        |not-sent    |
 |IPv6 Traffic Class |8 |1 |Bi|1             |equal        |not-sent    |
 |IPv6 Flow Label    |20|1 |Bi|144470        |equal        |not-sent    |
 |IPv6 Length        |16|1 |Bi|              |ignore       |compute-*   |
 |IPv6 Next Header   |8 |1 |Bi|17            |equal        |not-sent    |
 |IPv6 Hop Limit     |8 |1 |Bi|64            |equal        |not-sent    |
 |IPv6 DevPrefix     |64|1 |Bi|fe80::/64     |equal        |not-sent    |
 |IPv6 DevIID        |64|1 |Bi|::2           |equal        |not-sent    |
 |IPv6 AppPrefix     |64|1 |Bi|fe80::/64     |equal        |not-sent    |
 |IPv6 AppIID        |64|1 |Bi|::1           |equal        |not-sent    |
 +===================+==+==+==+==============+=============+============+
 |UDP DevPort        |16|1 |Bi|3865          |equal        |not-sent    |
 |UDP AppPort        |16|1 |Bi|5683          |equal        |not-sent    |
 |UDP Length         |16|1 |Bi|              |ignore       |compute-*   |
 |UDP Checksum       |16|1 |Bi|              |ignore       |compute-*   |
 +===================+==+==+==+==============+=============+============+
 |CoAP Version       |2 |1 |Bi|1             |equal        |not-sent    |
 |CoAP Type          |2 |1 |Up|2             |equal        |not-sent    |
 |CoAP TKL           |4 |1 |Bi|0             |equal        |not-sent    |
 |CoAP Code          |8 |1 |Up|[68, 128, 129,|match-mapping|mapping-sent|
 |                   |  |  |  | 132, 160]    |             |            |
 |CoAP MID           |16|1 |Bi|0             |MSB(9)       |LSB         |
 +===================+==+==+==+==============+=============+============+
~~~
{: #Fig-M4 title='Management Rule 4'}

# OSCORE

## Compression Rules

# DTLS

## Compression Rules


# Example CORECONF usage in Python

## Deletion cases

* Delete root element:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc'): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5100): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1811913ecf6

  RES: 2.04 Changed
  ~~~

* Delete a specific rule:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule', 0, 3): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5101, 0, 3): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1831913ed0003f6
  
  RES: 2.04 Changed
  ~~~
  
* Delete a specific protocol field entry:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry', 0, 3, 'fid-ipv6-version', 1, 'di-bidirectional'): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5105, 0, 3, 5068, 1, 5018): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913f100031913cc0119139af6
  
  RES: 2.04 Changed
  ~~~
  
* Delete a specific key:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/rule-status', 0, 3): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5137, 0, 3): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1831914110003f6

  RES: 2.04 Changed
  ~~~
  
* Delete a list element:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry/target-value/value', 0, 3, 'fid-ipv6-version', 1, 'di-bidirectional', 0): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5120, 0, 3, 5068, 1, 5018, 0): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a18719140000031913cc0119139a00f6
  
  RES: 2.04 Changed
  ~~~
  
* Delete a multiple list elements:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry/target-value/value', 0, 3, 'fid-ipv6-trafficclass', 1, 'di-bidirectional', 1): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5120, 0, 3, 5065, 1, 5018, 1): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a18719140000031913c90119139a01f6

  RES: 2.04 Changed
  ~~~
  
* Delete an unknown entry:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry', 2, 3, 'fid-ipv6-version', 1, 'di-bidirectional'): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5105, 2, 3, 5068, 1, 5018): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913f102031913cc0119139af6

  RES: 4.00 Bad Request
  ~~~
  
* Delete a protected key:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/rule-id-value', 0, 3): None
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5135, 0, 3): None
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a18319140f0003f6

  RES: 4.00 Bad Request
  ~~~

## Update cases

* Update protected key:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/rule-id-value', 0, 3): 5
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5135, 0, 3): 5
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a18319140f000305

  RES: 2.04 Changed
  ~~~

* Update a specific key:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/rule-status', 0, 3): 'status-candidate'
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5137, 0, 3): 5096
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a18319141100031913e8

  RES: 2.04 Changed
  ~~~

## Addition cases

* Add a new entry:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry', 0, 3, 'fid-ipv6-appprefix', 1, 'di-bidirectional'): {
        'field-length': 64, 
        'target-value': [{'index': 0, 'value': '/oAAAAAAAAA='}], 
        'matching-operator': 'ietf-schc:mo-equal', 
        'comp-decomp-action': 'ietf-schc:cda-not-sent'
    }
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5105, 0, 3, 5057, 1, 5018): {
        7: 64, 
        13: [{1: 0, 2: b'\xfe\x80\x00\x00\x00\x00\x00\x00'}], 
        9: 5083, 
        1: 5015
    }
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913f100031913c10119139aa40718400d81a201000248fe80000000000000091913db01191397
  
  RES: 2.04 Changed
  ~~~

* Add a list element (auto-indexed)
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry/target-value', 0, 3, 'fid-ipv6-flowlabel', 1, 'di-bidirectional'): {
        'index': 4, 'value': 'vLw='
    }
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5118, 0, 3, 5061, 1, 5018): {
        1: 4, 2: b'\xbc\xbc'
    }
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913fe00031913c50119139aa201040242bcbc

  RES: 2.04 Changed
  ~~~

* Add a list element (explicit index):
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry/target-value', 0, 3, 'fid-ipv6-flowlabel', 1, 'di-bidirectional'): {
        'index': 7, 'value': 'vLw='
    }
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5118, 0, 3, 5061, 1, 5018): {
        1: 7, 2: b'\xbc\xbc'
    }
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913fe00031913c50119139aa201070242bcbc

  RES: 2.04 Changed
  ~~~

* Add a new key–value pair element:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry/target-value', 0, 3, 'fid-ipv6-payload-length', 1, 'di-bidirectional'): [
        {'index': 0, 'value': 'UA=='}, 
        {'index': 1, 'value': 'VQ=='}
    ]
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5118, 0, 3, 5064, 1, 5018): [
        {1: 0, 2: b'\x50'}, {1: 1, 2: b'\x55'}
    ]
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913fe00031913c80119139a82a20100024150a20101024155

  RES: 2.04 Changed
  ~~~

* Add a new rule:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule', 5, 3): {
        'rule-status': 'ietf-schc:status-active', 
        'rule-id-value': 10, 
        'rule-id-length': 5, 
        'rule-nature': 'ietf-schc:nature-compression'
    }
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5101, 5, 3): {36: 5094, 34: 10, 33: 5, 35: 5088}
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1831913ed0503a418241913e618220a18210518231913e0

  RES: 2.04 Changed
  ~~~

* Add an entry into an unknown rule:
  
  ~~~
  YANG REQ: iPATCH /c
  {
    ('/ietf-schc:schc/rule/entry', 250, 8, 'fid-ipv6-payload-length', 1, 'di-bidirectional'): {
        'field-length': 16, 
        'matching-operator': 'ietf-schc:mo-ignore', 
        'comp-decomp-action': 'ietf-schc:cda-value-sent'
    }
  } 
  
  CORECONF REQ: iPATCH /c
  {
    (5105, 250, 8, 5064, 1, 5018): {7: 16, 9: 5084, 1: 5016}
  }
  
  REQ: iPATCH /c
      (Content-Format: application/yang-identifiers+cbor-seq)
  a1861913f118fa081913c80119139aa30710091913dc01191398

  RES: 4.00 Bad Request
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
