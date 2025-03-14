---
v: 3

title: Options representation in SCHC YANG Data Models
abbrev: SCHC for CoAP
docname: draft-toutain-schc-universal-option

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
      - name: Marco Tiloca
        org: RISE AB
        street: Isafjordsgatan 22
        city: Kista
        code: SE-16440
        country: Sweden
        email: marco.tiloca@ri.se
      - name: Laurent Toutain
        org: IMT Atlantique
        street: CS 17607, 2 rue de la Chataigneraie
        city: Cesson-Sevigne Cedex
        code: 35576
        country: France
        email: Laurent.Toutain@imt-atlantique.fr

normative:
  RFC8724:
  RFC9363:

informative:
  RFC8824:
  I-D.lampin-lpwan-schc-considerations:
  I-D.ietf-schc-8824-update:
  I-D.ietf-lpwan-architecture:
  GPC-SPE-207: 
    title: "Remote Application Management over CoAP – Amendment M v1.0"
    author:
       org: "GlobalPlatform"
    target: "https://globalplatform.org/specs-library/amendment-m-remote-application-mgmt-over-coap/"

entity:
  SELF: "[RFC-XXXX]"

--- abstract

The idea of keeping option identifiers in SCHC Rules simplifies the interoperability and the evolution of SCHC compression, when the protocol introduces new options, that can be unknown from the current SCHC implementation. This document discuss the augmentation of the current YANG Data Model, in order to add in the Rule options identifiers used by the protocol.


--- middle

# Introduction # {#intro}

Static Context Header Compression (SCHC) enables efficient communication in constrained networks by compressing protocol headers using predefined Rules. This document proposes improvements to how SCHC handles protocol options, as for CoAP (Constrained Application Protocol).


The Data Model defined in {{RFC9363}} was written based on LPWAN technologies while the working group was developing a solution for those devices. When the {{RFC9363}} was developed, the group targeted devices such as sensors and actuators with very constrained resources but these devices have very predictable traffic leading to very static rules. Also, the data model includes CoAP parameters defined in {{RFC8824}}.

# Current Challenges


Since CoAP is a more flexible protocol compared to IPv6 (without extensions) or UDP, given that CoAP includes options. The data model redefined these options as identifiers that are included in SCHC Rules as Field ID (FID).

If this approach was acceptable for LPWAN technologies that have a  static and controlled environment, the generalization of SCHC to more dynamic environment is a source of interoperability issues. Even though, this solution will become more accurate when rule management between two end-points in a SCHC instance is used to optimize compression.

The following scenario (cf. {{fig-rule-mngt}}) illustrates this issue and assumes that the traffic is CoAP based, even if this can be extended to other protocols with options.

~~~~ aasvg
              rule mngt
             +----------+
             |          |
             v          v
A <-------> S1 <~~~~~~> S2 <-----> B
~~~~
{: #fig-rule-mngt title="Rule Management between two SCHC end-points" artwork-align="center"}

In this scenario:

* Device A generates CoAP packets with various options.
* SCHC nodes S1 and S2 compress and decompress the traffic using shared Rules.
* When A uses a newly defined or private option, S1 can derive new Rules to optimize compression, including this option.
* The challenge lies in communicating these new Field IDs (FIDs) to S2

Suppose that a Rule defines just a CoAP header, and a more specific Rule is derived including a URI-path. The entry (cf. {{fig-entry-uri-path}}) is present in the derived Rule. {{RFC9363}} defines identityref for several elements, (respectively fid:coap-option-uri-path, di:up, mo:equal and cda:not-sent) that can be used to send the Rule description to the other side.

~~~~ aasvg
+--------------+-----+---+----+-------+-------+---------+
|    FID       | FL  | FP| DI |  TV   |   MO  |   CDA   |
+==============+=====+===+====+=======+=======+=========+
| ...          | ... |...|... | ...   | ...   | ...     |
|CoAP.Uri-path | len | 1 | up | value | equal | not-sent|
+--------------+-----+---+----+-------+-------+---------+
~~~~
{: #fig-entry-uri-path title="New entry added by management" artwork-align="center"}

Now suppose that A uses a recently defined option or a private option. In S1, nothing is changed, the CoAP header is parsed, the new option is discovered, and a Rule is derived to compress the option. The only blocking element is the identification of this new FID in the Rule and how S1 sends it to the other end-point to understand which option is involved (cf {{fig-new-fid}}) and what is the value for reconstructing the header.

~~~~ aasvg
+---------------+-----+---+----+-------+-------+---------+
|     FID       | FL  | FP| DI |  TV   |   MO  |   CDA   |
+===============+=====+===+====+=======+=======+=========+
| ...           | ... |...|... | ...   | ...   | ...     |
|CoAP.new-option| len | 1 | up | value | equal | not-sent|
+---------------+-----+---+----+-------+-------+---------+
~~~~
{: #fig-new-fid title="New entry added by management" artwork-align="center"}

In fact, the way FIDs are allocated using a YANG Data Model cannot be used when some fields are defined after the SCHC implementation. The Parser will identify this new option since the structure in the header remains the same. The compression and decompression do not need to be modified, since it is based in generic procedure. The problem is related to FID allocation, internally to the SCHC implementation and to the Data Model to exchange Rules with other implementations.

The protocol option space and the SCHC FID space are not correlated, this leads to an interoperability issue.

# Syntactic compression

SCHC compression is semantic, field ID are abstracted in a generic representation composed of a field ID, a position, and a direction. For instance, when a CoAP option is sent on the wire, the option is coded as a delta option, a length value and the value. All these information is found in the abstract description. The delta option allows to find the option number which is turned into a SCHC FID, the length is taken from the option as the associated value.  As stated before, the mapping between the option number and the FID must be known and failed if the option is new to the SCHC implementation.

To avoid the mapping between a protocol ID and a SCHC ID {{I-D.lampin-lpwan-schc-considerations}} proposed,  to stay closer to the protocol syntax and define Rules that will take into account the option format. So, an option will be described in 3 fields (cf. {{fig-synt-not-sent}}):

~~~~ aasvg
+------------+-----+---+----+-------+-------+---------+
|     FID    | FL  | FP| DI |  TV   |   MO  |   CDA   |
+============+=====+===+====+=======+=======+=========+
|CoAP.option | 16  | 1 | up | opt or| equal | not-sent|
|            |     |   |    | delta |       |         |
|CoAP.length | 16  | 1 | up | value | equal | not-sent|
|CoAP.value  | len | 1 | up | value | equal | not-sent|
+------------+-----+---+----+-------+-------+---------+
~~~~
{: #fig-synt-not-sent title="representation of an elided option with syntactic representation" artwork-align="center"}
Where option could be either the absolute CoAP option number or the delta as it appears in the CoAP message. This way, the option remains in the CoAP numbering space and every option is processed the same way and upcoming options will also be compressed.

Nevertheless, this encoding multiply by three the number of entries to describe an option, leading to a larger representation of the Rule. If this description works well when the field is elided with not-sent CDA, the compression is more complex when the option must be sent. For instance (cf. {{fig-sem-value-sent}}):

~~~~ aasvg
+---------------+---+---+--+-----+------+----------+
|      FID      |FL |FP |DI| TV  |  MO  |   CDA    |
+===============+===+===+==+=====+======+==========+
|CoAP.new-option|var| 1 |up|value|equal |value-sent|
+---------------+---+---+--+-----+------+----------+
~~~~
{: #fig-sem-value-sent title="representation of an option sent with semantic representation" artwork-align="center"}

will be transformed into (cf. {{fig-snyt-value-sent}}):

~~~~ aasvg
+------------+---+--+--+--+------+----------+
|    FID     |FL |FP|DI|TV|  MO  |   CDA    |
+============+===+==+==+==+======+==========+
|CoAP.option |16 |1 |up|  |ignore|value-sent|
|CoAP.length |16 |1 |up|  |ignore|value-sent|
|CoAP.value  |var|1 |up|  |ignore|value-sent|
+------------+---+--+--+--+------+----------+
~~~~
{: #fig-snyt-value-sent title="representation of an option sent with syntactic representation" artwork-align="center"}

In that case, the option or the length coded from 4 bits to 16 bits may be viewed as a 16-bit field that has to be sent as residue. The option length has to be sent twice, the first time in the CoAP.length field and a second time in the residue of the value. To avoid this, one option could have been to define a new length function, linking the length of the value to the content of the CoAP.length field. Without this optimization, if we want to keep it generic, an option of 4 bytes, will be coded 2+2+0.5+3 = 7.5 bytes.

Having generic compression schemes is interesting and this work needs to continue to be investigated, but going too close to the byte representation may lead to suboptimal compression and Rule representation.

# Options ID

The idea of keeping   protocol identifiers in SCHC Rules simplify the interoperability and the evolution of SCHC compression, when the protocol evolves. One solution is to use these identifiers in the compression Rules. Since several protocols may reuse the same values. For instance, option 8 refers to Location-Path in CoAP and Timestamp in TCP. The value must be associated with the protocol to avoid ambiguities.

One solution could be to define in SCHC an identity referring to the protocol, followed by the value used by this protocol.

The tree (cf. {{fig-yang-rule-entry}}) shows how compression rules are defined in the YANG Data Model {{RFC9363}}:

~~~~
           +--:(compression) {compression}?
              +--rw entry* [field-id field-position direction-indicator]
                 +--rw field-id                    schc:fid-type
                 +--rw field-length                union
                 +--rw field-position              uint8
                 +--rw direction-indicator         schc:di-type
                 .
                 .
                 .
~~~~
{: #fig-yang-rule-entry title="Rule entry defined by [RFC 9363]." artwork-align="center"}

An entry is defined by a key composed of the field-id, a field-position and the direction indicator. This branch of the tree cannot be augmented with a new leaf containing the option value and the field-id set to an identifier specifying the CoAP options.

For instance, the representation of an URI with two path elements (11) and two query elements (15):

~~~~ aasvg
+---------------+---+--+--+-----+------+----------+
|      FID      |FL |FP|DI| TV  |  MO  |   CDA    |
+===============+===+==+==+=====+======+==========+
|CoAP.option(11)|len|1 |up|value|equal |not-sent  |
|CoAP.option(11)|len|2 |up|     |ignore|value-sent|
|CoAP.option(15)|len|1 |up|value|equal |not-sent  |
|CoAP.option(15)|len|2 |up|value|equal |not-sent  |
+---------------+---+--+--+-----+------+----------+
~~~~
{: #fig-proto-id title="Rule including options ID." artwork-align="center"}

Is not valid regarding the Data Model, since the key FID, position, direction is repeated four times on the example. The option itself must be included as a key.

It is not possible to augment the model defined in RFC 9363 and add this leaf to the key of the list. Having this element on all entries is not also optimal. It looks better to augment the current compression data model with another list containing entries describing options.

~~~~
  +--rw schc-opt:entry-option-space* \
          [space-id option-value field-position direction-indicator]
    +--rw schc-opt:space-id                    space-type
    +--rw schc-opt:option-value                uint32
    +--rw schc-opt:field-length                union
    +--rw schc-opt:field-position              uint8
    +--rw schc-opt:direction-indicator         schc:di-type
    .
    .
    .
~~~~
{: #fig-augmentation-id title="Augmentation of SCHC Data Model to include options ID." artwork-align="center"}

The space-id defines the protocol space, this value may be provided by the SCHC WG and option-value is taken from the protocol space maintained by IANA.

This will have an impact on the serialization of residues. Both ends must have the entry in the same order. So Field from “entry” list MUST be serialized before the ones defined in “entry-option-space”.

# Impact on current standards

{{RFC9363}} and {{I-D.ietf-schc-8824-update}} define some FID for CoAP options. This leads to have similar Rule but they are incompatible. CoAP option identifier should be deprecated.


This leads also to a constraint that has not been included for the Data Model. The order of the Field Descriptors is not specified as YANG do not impose a position in a list. This has no impact on the compression process but is important for the serialization. The {{I-D.ietf-lpwan-architecture}} should document the fact that entry ordrer should not be changed when transmitted from one end-point to the other. So, this allow to keep the indication of {{RFC8724}} to keep Field Descriptors (aka entries) listed in the order they appear in the packet header.




--- back


# YANG Data Model

This appendix defines the work in progress YANG Data Model to extend the Data Model defined in {{RFC9363}}.

~~~~~~~~~~~ yang
module ietf-schc-opt {
  yang-version 1.1;
  namespace "urn:ietf:params:xml:ns:yang:ietf-schc-opt";
  prefix schc-opt;

  import ietf-schc {
      prefix schc;
  }

  organization
    "IETF IPv6 over Low Power Wide-Area Networks (lpwan) working group";
  contact
    "WG Web:   <https://datatracker.ietf.org/wg/lpwan/about/>
     WG List:  <mailto:p-wan@ietf.org>
     Editor:   Laurent Toutain
       <mailto:laurent.toutain@imt-atlantique.fr>
     Editor:   Ana Minaburo
       <mailto:ana@ackl.io>";
  description
     "
     Copyright (c) 2021 IETF Trust and the persons identified as
     authors of the code.  All rights reserved.

     Redistribution and use in source and binary forms, with or
     without modification, is permitted pursuant to, and subject to
     the license terms contained in, the Simplified BSD License set
     forth in Section 4.c of the IETF Trust's Legal Provisions
     Relating to IETF Documents
     (https://trustee.ietf.org/license-info).

     This version of this YANG module is part of RFC XXXX
     (https://www.rfc-editor.org/info/rfcXXXX); see the RFC itself
     for full legal notices.

     The key words 'MUST', 'MUST NOT', 'REQUIRED', 'SHALL', 'SHALL
     NOT', 'SHOULD', 'SHOULD NOT', 'RECOMMENDED', 'NOT RECOMMENDED',
     'MAY', and 'OPTIONAL' in this document are to be interpreted as
     described in BCP 14 (RFC 2119) (RFC 8174) when, and only when,
     they appear in all capitals, as shown here.

     *************************************************************************

     This module extends the ietf-schc module to include the compound-ack
     behavior for Ack On Error as defined in RFC YYYY.
     It introduces a new leaf for Ack on Error defining the format of the
     SCHC Ack and add the possibility to send several bitmaps in a single
     answer.";

  revision 2024-12-19 {
    description
      "Initial version for RFC YYYY ";
    reference
      "RFC YYYY: OAM";
  }


  identity space-id-base-type {
    description
      "Field ID base type for all fields.";
  }

  identity space-id-coap {
    base space-id-base-type;
    description
      "Field ID base type for IPv6 headers described in RFC 8200.";
    reference
      "RFC 8200 Internet Protocol, Version 6 (IPv6) Specification";
  }

  typedef space-type {
    type identityref {
      base space-id-base-type;
    }
    description
      "Field ID generic type.";
    reference
      "RFC 8724 SCHC: Generic Framework for Static Context Header
                Compression and Fragmentation";
  }


 augment "/schc:schc/schc:rule/schc:nature/schc:compression" {
  list entry-option-space {
    key "space-id option-value field-position direction-indicator";
    leaf space-id {
      type space-type;
      mandatory true;
      description
        "";
    }
    leaf option-value {
      type uint32;
    }
    leaf field-length {
      type union {
      type uint8;
      type schc:fl-type;
        }
      mandatory true;
      description
        "Field Length, expressed in number of bits if the length is
         known when the Rule is created or through a specific
         function if the length is variable.";
    }
    leaf field-position {
      type uint8;
      mandatory true;
      description
        "Field Position in the header is an integer.  Position 1
         matches the first occurrence of a field in the header,
         while incremented position values match subsequent
         occurrences.
         Position 0 means that this entry matches a field
         irrespective of its position of occurrence in the
         header.
         Be aware that the decompressed header may have
         position-0 fields ordered differently than they
         appeared in the original packet.";
    }
    leaf direction-indicator {
      type schc:di-type;
      mandatory true;
      description
        "Direction Indicator, indicate if this field must be
         considered for Rule selection or ignored based on the
         direction (bidirectional, only uplink, or only
         downlink).";
    }
    list target-value {
      key "index";
      uses schc:tv-struct;
      description
        "A list of values to compare with the header field value.
         If Target Value is a singleton, position must be 0.
         For use as a matching list for the mo-match-mapping Matching
         Operator, index should take consecutive values starting
         from 0.";
    }
    leaf matching-operator {
      type schc:mo-type;
      must "../target-value or derived-from-or-self(.,
                                                   'mo-ignore')" {
        error-message
          "mo-equal, mo-msb, and mo-match-mapping need target-value";
        description
          "target-value is not required for mo-ignore.";
      }
      must "not (derived-from-or-self(., 'mo-msb')) or
            ../matching-operator-value" {
        error-message "mo-msb requires length value";
      }
      mandatory true;
      description
        "MO: Matching Operator.";
      reference
        "RFC 8724 SCHC: Generic Framework for Static Context Header
                  Compression and Fragmentation (see Section 7.3)";
    }
    list matching-operator-value {
      key "index";
      uses schc:tv-struct;
      description
        "Matching Operator Arguments, based on TV structure to allow
         several arguments.
         In RFC 8724, only the MSB Matching Operator needs arguments
         (a single argument, which is the number of most significant
         bits to be matched).";
    }
    leaf comp-decomp-action {
      type schc:cda-type;
      must "../target-value or
                derived-from-or-self(., 'cda-value-sent') or
                derived-from-or-self(., 'cda-compute') or
                derived-from-or-self(., 'cda-appiid') or
                derived-from-or-self(., 'cda-deviid')" {
        error-message
          "cda-not-sent, cda-lsb, and cda-mapping-sent need
           target-value";
        description
          "target-value is not required for some CDA.";
        }
      mandatory true;
      description
        "CDA: Compression Decompression Action.";
      reference
        "RFC 8724 SCHC: Generic Framework for Static Context Header
                  Compression and Fragmentation (see Section 7.4)";
    }
    list comp-decomp-action-value {
      key "index";
      uses schc:tv-struct;
      description
        "CDA arguments, based on a TV structure, in order to allow
         for several arguments.  The CDAs specified in RFC 8724
         require no argument.";
    }
  }

  }
}
~~~~~~~~~~~
{: sourcecode-name="ietf-schc-opt@2024-12-19.yang" sourcecode-markers="true"}

# Examples

The following message is a CoAP message with several options, options are defined in {{RFC9363}}, except SCP82-Param (2055):

~~~~
0000  40 01 00 01 BD 01 61 63 63 65 6C 65 72 6F 6D 65  @.....accelerome
0010  74 65 72 73 07 6D 61 78 69 6D 75 6D 4A 64 61 74  ters.maximumJdat
0020  65 3D 74 6F 64 61 79 0A 75 6E 69 74 3D 6D 2F 73  e=today.unit=m/s
0030  5E 32 21 3C D1 E4 02 E3 05 F8 54 4C 56           ^2!<......TLV

CON  0x0001 GET   
> Uri-path : b'accelerometers'
> Uri-path : b'maximum'
> Uri-query : b'date=today'
> Uri-query : b'unit=m/s^2'
> Accept : 60
> No-Response : 2
> SCP82-Param : b'TLV'
~~~~
{: #fig-coap-example title="Example of a CoAP packet with options." artwork-align="center"}

In the following examples, the compression rule will send the residues for the Uri-Path, Uri-Query and SCP82-Param, 
the rest is elided.

The goal of the comparison is to see:

* the size of the serialization of a rule matching the previous packet
* the size of the CORECONF query payload to access to the Target Value of the Accept option in the rule.
* the size of the compressed message

## Semantic compression

In RFC8724 informal notation, a rule matching this packet could be:

~~~~~
+===================================================================+
|RuleID 1/8                                                         |
+==========+===+==+==+======+===============+===============+=======+
|  Field   | FL|FP|DI|  TV  |       MO      |      CDA      |  Sent |
|          |   |  |  |      |               |               | [bits]|
+==========+===+==+==+======+===============+===============+=======+
|CoAP      |2  |1 |Bi|01    | equal         | not-sent      |       |
|version   |   |  |  |      |               |               |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Type |2  |1 |Dw|CON   | equal         | not-sent      |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP TKL  |4  |1 |Bi|0     | equal         | not-sent      |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Code |8  |1 |DW|0.01  | equal         | not-sent      |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP MID  |16 |1 |Bi|0000  | MSB(7)        | LSB           |MID    |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Uri- |var|1 |Dw|      | ignore        | value-sent    | size+ |
|Path      |   |  |  |      |               |               | value |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Uri- |var|2 |Dw|      | ignore        | value-sent    | size+ |
|Path      |   |  |  |      |               |               | value |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Uri- |var|1 |Dw|      | ignore        | value-sent    | size+ |
|Query     |   |  |  |      |               |               | value |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP Uri- |var|2 |Dw|      | ignore        | value-sent    | size+ |
|Query     |   |  |  |      |               |               | value |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP      |8  |1 |Dw| 60   | equal         | not-sent      |       |
|Accept    |   |  |  |      |               |               |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP  No- |8  |1 |Dw| 2    | equal         | not-sent      |       |
|Response  |   |  |  |      |               |               |       |
+----------+---+--+--+------+---------------+---------------+=======+
|CoAP  SCP |var|1 |Dw|      | ignore        | value-sent    | size+ |
|82-Param  |   |  |  |      |               |               | value |
+----------+---+--+--+------+---------------+---------------+=======+

~~~~~
{: #fig-rule-test title="Target rule." artwork-align="center"}

### with RFC 9363 

The rule 1/8 cannot be serialized in CBOR with {{RFC9363}} Data Model, since
there is indentyref defined for CoAP SCP82 Param option. This could be solved 
by defining a new YANG DM introducing identityref for the options defined for 
{{GPC-SPE-207}} and the associated SID range. We suppose that {{RFC9363}} SIDs
starts at 5000 and {{GPC-SPE-207}} at 10000. 

The CBOR message is 357 bytes long as shown {{fig-cbor-serial}}.

~~~~~
b'a11913e7a10181a4048ca7061913bf070208010519139b091913db011913970d81a20100024101a7
061913be070208010519139a091913db011913970d81a20100024100a7061913bc070408010519139b
091913db011913970d81a20100024100a70619139f070808010519139a091913db011913970d81a201
00024101a8061913a2071008010519139a091913de0a81a20100024107011913950d81a20100024100
a6061913b907d82d1913d508010519139b091913dc01191398a6061913b907d82d1913d50802051913
9b091913dc01191398a6061913bb07d82d1913d508010519139b091913dc01191398a6061913bb07d8
2d1913d508020519139b091913dc01191398a7061913a4070808010519139b091913db011913970d81
a2010002413ca7061913ae070808010519139b091913db011913970d81a20100024102a60619271107
d82d1913d508010519139b091913dc0119139818220818210818231913e0'
~~~~~
{: #fig-cbor-serial title="CBOR serialisation." artwork-align="center"}

The diagnostic representation of the CBOR message is the following:

~~~~
Deltas in entry part:
- 6: field-id
- 7: field-length
- 8: field-position
- 5: direction-indicator
- 9: matching-operator
- 1: comp-decomp-action
- 10: matching-operator-value
- 13: target-value

Deltas in the rule part:
- 33: rule-id-length
- 34: rule-id-value
- 35: rule-nature

{5095: {1: [{4: [
  {6: 5055, 7: 2, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'01'}]}, 
  {6: 5054, 7: 2, 8: 1, 5: 5018, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'00'}]}, 
  {6: 5052, 7: 4, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'00'}]}, 
  {6: 5023, 7: 8, 8: 1, 5: 5018, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'01'}]}, 
  {6: 5026, 7: 16, 8: 1, 5: 5018, 9: 5086, 
                10: [{1: 0, 2: h'07'}], 1: 5013, 13: [{1: 0, 2: h'00'}]}, 
  {6: 5049, 7: 45(5077), 8: 1, 5: 5019, 9: 5084, 1: 5016}, 
  {6: 5049, 7: 45(5077), 8: 2, 5: 5019, 9: 5084, 1: 5016}, 
  {6: 5051, 7: 45(5077), 8: 1, 5: 5019, 9: 5084, 1: 5016}, 
  {6: 5051, 7: 45(5077), 8: 2, 5: 5019, 9: 5084, 1: 5016}, 
  {6: 5028, 7: 8, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'3C'}]}, 
  {6: 5038, 7: 8, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'02'}]}, 
  {6: 10001, 7: 45(5077), 8: 1, 5: 5019, 9: 5084, 1: 5016}], 
34: 8, 33: 8, 35: 5088}]}}
~~~
{: #fig-cbor-diag title="CBOR diagnostic notation." artwork-align="center"}

Note that the coding of rule-id-value, rule-id-lenght and rule-nature is not optimal, 
since the delta is higher than 23, and correspond to 2 bytes in the CBOR encoding.

CORECONF request to access to the target value of the Accept option is given in {{fig-query}}. The size of the CoAP payload is 14 bytes.

~~~
REQ: FETCH </c>
        (Content-Format: application/yang-identifiers+cbor-seq)
   [5115,     / .../target-value/value 
    8,        / rule-id-value
    1,        / rule-id-length
    5028,     / fid-coap-option-accept
    1,        / field-position
    5019,     / direction-indicator
    0]        / target-value/index
~~~
{: #fig-query title="CORECONF query to Accept TV." artwork-align="center"}

The SCHC packet {{fig-residue}} has a size of 389 bits or 49 bytes with the alignment.

~~~
0800f30b1b1b2b632b937b6b2ba32b939bb6b0bc34b6bab6d3230ba329eba37b230bcd3ab734ba1eb697b9af191aa262b0/389
~~~
{: #fig-residue title="SCHC compressed packet." artwork-align="center"}


### Universal Options (Laurent)

We assign SIDs starting from 7000 to the YANG DM augmentation defined in this document. All the CoAP options are defined by a space ID indicating CoAP and the option number used in CoAP. Option CSP82-Param is processed like any other options. 

The CBOR message is 481 bytes long as shown {{fig-cbor-serial}}.

~~~
b'a11913e7a10181a4048ca7061913bf070208010519139b091913db011913970d81a20100024101a7
061913be070208010519139a091913db011913970d81a20100024100a7061913bc070408010519139b
091913db011913970d81a20100024100a70619139f070808010519139a091913db011913970d81a201
00024101a8061913a2071008010519139a091913de0a81a20100024107011913950d81a20100024100
a719077c191b5a19077b0b190775d82d1913d51907760119077419139b1907771913dc190770191398
a719077c191b5a19077b0b190775d82d1913d51907760219077419139b1907771913dc190770191398
a719077c191b5a19077b0f190775d82d1913d51907760119077419139b1907771913dc190770191398
a719077c191b5a19077b0f190775d82d1913d51907760219077419139b1907771913dc190770191398
a819077c191b5a19077b11190775081907760119077419139b1907771913db19077019139719077d81
a2010002413ca819077c191b5a19077b190102190775d82d1913d51907760119077419139b19077719
13db19077019139719077d81a20100024102a719077c191b5a19077b190807190775d82d1913d51907
760119077419139b1907771913dc19077019139818220818210818231913e0'
~~~
{: #fig-cbor-serial2 title="CBOR serialisation." artwork-align="center"}

The diagnostic representation of the CBOR message is the following:

~~~
Deltas in entry part:
- 6: field-id                     **1916: space-id  
- 7: field-length                 **1915: option-value 
- 8: field-position               **1909: field-length
- 5: direction-indicator          **1910: field-position
- 9: matching-operator            **1908: direction-indicator
- 1: comp-decomp-action           **1911: matching-operator  
- 10: matching-operator-value     **1917: target-value
- 13: target-value                

Deltas in the rule part:
* 33: rule-id-length
* 34: rule-id-value
* 35: rule-nature

{5095: {1: [{4: [
  {6: 5055, 7: 2, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'01'}]}, 
  {6: 5054, 7: 2, 8: 1, 5: 5018, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'00'}]}, 
  {6: 5052, 7: 4, 8: 1, 5: 5019, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'00'}]}, 
  {6: 5023, 7: 8, 8: 1, 5: 5018, 9: 5083, 1: 5015, 13: [{1: 0, 2: h'01'}]}, 
  {6: 5026, 7: 16, 8: 1, 5: 5018, 9: 5086, 
                    10: [{1: 0, 2: h'07'}], 1: 5013, 13: [{1: 0, 2: h'00'}]}, 
  {1916: 7002, 1915: 11, 1909: 45(5077), 1910: 1, 1908: 5019, 1911: 5084, 1904: 5016}, 
  {1916: 7002, 1915: 11, 1909: 45(5077), 1910: 2, 1908: 5019, 1911: 5084, 1904: 5016}, 
  {1916: 7002, 1915: 15, 1909: 45(5077), 1910: 1, 1908: 5019, 1911: 5084, 1904: 5016}, 
  {1916: 7002, 1915: 15, 1909: 45(5077), 1910: 2, 1908: 5019, 1911: 5084, 1904: 5016}, 
  {1916: 7002, 1915: 17, 1909: 8, 1910: 1, 1908: 5019, 1911: 5083, 1904: 5015, 
                                                1917: [{1: 0, 2: h'3C'}]}, 
  {1916: 7002, 1915: 258, 1909: 45(5077), 1910: 1, 1908: 5019, 1911: 5083, 1904: 5015, 
                                                1917: [{1: 0, 2: h'02'}]},
  {1916: 7002, 1915: 2055, 1909: 45(5077), 1910: 1, 1908: 5019, 1911: 5084, 1904: 5016}], 
34: 8, 33: 8, 35: 5088}]}}
~~~
{: ##fig-cbor-diag2  title="CBOR serialisation." artwork-align="center"}

It can be noted that the CoAP options part, delta are very large and takes 3 bytes for
encode then in CBOR. We uses another range of SIDs for the augmentation, based on the
standard allocation procedure, where each YANG DM has its own range. 

CORECONF request to access to the target value of the Accept option is given in {{fig-query}}. The size of the CoAP payload is 15 bytes.

~~~
REQ: FETCH </c>
        (Content-Format: application/yang-identifiers+cbor-seq)
   [7019,     / .../target-value/value 
    8,        / rule-id-value
    1,        / rule-id-length
    7002,     / space-id-value
    17,       / option-value
    1,        / field-position
    5019,     / direction-indicator
    0]        / target-value/index
~~~
{: #fig-query2 title="CORECONF query to Accept TV." artwork-align="center"}

## Merged

Instead of having two Data Models, RFC9363 and Universal Options defined in this document are merged into
single Data Model, called 9363bis. The SID allocation process remains inchanged and SID are allocated automatically
using the numbering based on alphabetical order.

The CBOR serialization leads to 400 Bytes of data.
~~~
b'a11913e9a10181a4048ca7171913bf1818021819011619139b181a1913db12191397181e81a20100
024101a7171913be1818021819011619139a181a1913db12191397181e81a20100024100a7171913bc
1818041819011619139b181a1913db12191397181e81a20100024100a71719139f1818081819011619
139a181a1913db12191397181e81a20100024101a8171913a21818101819011619139a181a1913de18
1b81a2010002410712191395181e81a20100024100a70e1913e60d0b07d82d1913d508010619139b09
1913dc02191398a70e1913e60d0b07d82d1913d508020619139b091913dc02191398a70e1913e60d0f
07d82d1913d508010619139b091913dc02191398a70e1913e60d0f07d82d1913d508020619139b0919
13dc02191398a80e1913e60d11070808010619139b091913db021913970f81a2010002413ca80e1913
e60d19010207d82d1913d508010619139b091913db021913970f81a20100024102a70e1913e60d1908
0707d82d1913d508010619139b091913dc0219139818330818320818341913e0'
~~~
{: #fig-cbor-serial3 title="CBOR serialisation." artwork-align="center"}

They can be represented in the diagnostic notation 
~~~
Deltas in entry part:
- 23: field-id                     -14: space-id  
* 24: field-length                 -11: option-value 
* 25: field-position               -7: field-length
- 22: direction-indicator          -8: field-position
* 26: matching-operator            -6: direction-indicator
- 18: comp-decomp-action           -9: matching-operator  
* 27: matching-operator-value      -15: target-value
* 30: target-value                 

Deltas in the rule part:
* 50: rule-id-length
* 51: rule-id-value
* 52: rule-nature

{5097: {1: [{4: [
  {23: 5055, 24: 2, 25: 1, 22: 5019, 26: 5083, 18: 5015, 30: [{1: 0, 2: h'01'}]}, 
  {23: 5054, 24: 2, 25: 1, 22: 5018, 26: 5083, 18: 5015, 30: [{1: 0, 2: h'00'}]}, 
  {23: 5052, 24: 4, 25: 1, 22: 5019, 26: 5083, 18: 5015, 30: [{1: 0, 2: h'00'}]}, 
  {23: 5023, 24: 8, 25: 1, 22: 5018, 26: 5083, 18: 5015, 30: [{1: 0, 2: h'01'}]}, 
  {23: 5026, 24: 16, 25: 1, 22: 5018, 26: 5086, 
                       27: [{1: 0, 2: h'07'}], 18: 5013, 30: [{1: 0, 2: h'00'}]}, 
  {14: 5094, 13: 11, 7: 45(5077), 8: 1, 6: 5019, 9: 5084, 2: 5016}, 
  {14: 5094, 13: 11, 7: 45(5077), 8: 2, 6: 5019, 9: 5084, 2: 5016}, 
  {14: 5094, 13: 15, 7: 45(5077), 8: 1, 6: 5019, 9: 5084, 2: 5016}, 
  {14: 5094, 13: 15, 7: 45(5077), 8: 2, 6: 5019, 9: 5084, 2: 5016}, 
  {14: 5094, 13: 17, 7: 8, 8: 1, 6: 5019, 9: 5083, 2: 5015, 
                                                      15: [{1: 0, 2: h'3C'}]}, 
  {14: 5094, 13: 258, 7: 45(5077), 8: 1, 6: 5019, 9: 5083, 2: 5015, 
                                                      15: [{1: 0, 2: h'02'}]}, 
  {14: 5094, 13: 2055, 7: 45(5077), 8: 1, 6: 5019, 9: 5084, 2: 5016}], 
51: 8, 50: 8, 52: 5088}]}}
~~~
{: #fig-cbor-diag3  title="CBOR serialisation." artwork-align="center"}

I can be noted that some delta values are higher than 23, leading to a 2 bytes encoding in
CBOR.

Query and compressed packet are not represented, since the result are the same. The ID in the
query may differs since the SID allocation may be slightly different, but the size is unchanged.

## Ordered 

This time the SID file is manually edited to optimize the delta values. The Data Model is
exactly the same as in the previous example.

The CBOR serialization is 376 Byte long, 16 bytes longuer than the RFC 9363 with
specific SIDs for CoAP option.

~~~
b'a119139fa11781a4178ca71719142228022701161913fe2619143e121913fa2281a20100024101a7
1719142128022701161913fd2619143e121913fa2281a20100024100a71719141f28042701161913fe
2619143e121913fa2281a20100024100a71719140228082701161913fd2619143e121913fa2281a201
00024101a81719140528102701161913fd261914412581a20100024107121913f82281a20100024100
a70e1914490d0b07d82d1914380801061913fe0919143f021913fba70e1914490d0b07d82d19143808
02061913fe0919143f021913fba70e1914490d0f07d82d1914380801061913fe0919143f021913fba7
0e1914490d0f07d82d1914380802061913fe0919143f021913fba80e1914490d1107080801061913fe
0919143e021913fa0f81a2010002413ca80e1914490d19010207d82d1914380801061913fe0919143e
021913fa0f81a20100024102a70e1914490d19080707d82d1914380801061913fe0919143f021913fb
2a0829082b191443
~~~
{: #fig-cbor-serial4 title="CBOR serialisation." artwork-align="center"}

The diagnostic notation, shows that with positive and negative deltas, they can
be coded on a single byte.

~~~
Deltas in entry part:
- 23: field-id                     -14: space-id  
* -9: field-length                 -11: option-value 
* -8: field-position               -7: field-length
- 22: direction-indicator          -8: field-position
* -7: matching-operator            -6: direction-indicator
- 18: comp-decomp-action           -9: matching-operator  
* -6: matching-operator-value      -15: target-value
* -3: target-value                 

Deltas in the rule part:
* -11: rule-id-length
* -10: rule-id-value
* -12: rule-nature

{5023: {23: [{23: [
  {23: 5154, -9: 2, -8: 1, 22: 5118, -7: 5182, 18: 5114, -3: [{1: 0, 2: h'01'}]}, 
  {23: 5153, -9: 2, -8: 1, 22: 5117, -7: 5182, 18: 5114, -3: [{1: 0, 2: h'00'}]}, 
  {23: 5151, -9: 4, -8: 1, 22: 5118, -7: 5182, 18: 5114, -3: [{1: 0, 2: h'00'}]}, 
  {23: 5122, -9: 8, -8: 1, 22: 5117, -7: 5182, 18: 5114, -3: [{1: 0, 2: h'01'}]}, 
  {23: 5125, -9: 16, -8: 1, 22: 5117, -7: 5185, 
                       -6: [{1: 0, 2: h'07'}], 18: 5112, -3: [{1: 0, 2: h'00'}]}, 
  {14: 5193, 13: 11, 7: 45(5176), 8: 1, 6: 5118, 9: 5183, 2: 5115}, 
  {14: 5193, 13: 11, 7: 45(5176), 8: 2, 6: 5118, 9: 5183, 2: 5115}, 
  {14: 5193, 13: 15, 7: 45(5176), 8: 1, 6: 5118, 9: 5183, 2: 5115}, 
  {14: 5193, 13: 15, 7: 45(5176), 8: 2, 6: 5118, 9: 5183, 2: 5115}, 
  {14: 5193, 13: 17, 7: 8, 8: 1, 6: 5118, 9: 5182, 2: 5114, 
                                                         15: [{1: 0, 2: h'3C'}]}, 
  {14: 5193, 13: 258, 7: 45(5176), 8: 1, 6: 5118, 9: 5182, 2: 5114, 
                                                         15: [{1: 0, 2: h'02'}]}, 
  {14: 5193, 13: 2055, 7: 45(5176), 8: 1, 6: 5118, 9: 5183, 2: 5115}],
-11: 8, -10: 8, -12: 5187}]}}
~~~
{: #fig-cbor-diag4  title="CBOR serialisation." artwork-align="center"}

{{fig-sid-assignation}} shows how SIDs where manually allocated.  

~~~
5023;data;/ietf-schc:schc
...
5030;data;/ietf-schc:schc/rule/window-size
5031;data;/ietf-schc:schc/rule/w-size
5032;data;/ietf-schc:schc/rule/tile-size
5033;data;/ietf-schc:schc/rule/tile-in-all-1
5034;data;/ietf-schc:schc/rule/rule-nature
5035;data;/ietf-schc:schc/rule/rule-id-value
5036;data;/ietf-schc:schc/rule/rule-id-length
5037;data;/ietf-schc:schc/rule/retransmission-timer/ticks-numbers
5038;data;/ietf-schc:schc/rule/retransmission-timer/ticks-duration
5039;data;/ietf-schc:schc/rule/retransmission-timer
5040;data;/ietf-schc:schc/rule/rcs-algorithm
5041;data;/ietf-schc:schc/rule/maximum-packet-size
5042;data;/ietf-schc:schc/rule/max-interleaved-frames
5043;data;/ietf-schc:schc/rule/dtag-size
5044;data;/ietf-schc:schc/rule/direction
5045;data;/ietf-schc:schc/rule/ack-behavior
5046;data;/ietf-schc:schc/rule
5047;data;/ietf-schc:schc/rule/fcn-size
5048;data;/ietf-schc:schc/rule/fragmentation-mode
5049;data;/ietf-schc:schc/rule/inactivity-timer
5050;data;/ietf-schc:schc/rule/inactivity-timer/ticks-duration
5051;data;/ietf-schc:schc/rule/inactivity-timer/ticks-numbers
5052;data;/ietf-schc:schc/rule/l2-word-size
5053;data;/ietf-schc:schc/rule/max-ack-requests
...
5060;data;/ietf-schc:schc/rule/entry/field-length
5061;data;/ietf-schc:schc/rule/entry/field-position
5062;data;/ietf-schc:schc/rule/entry/matching-operator
5063;data;/ietf-schc:schc/rule/entry/matching-operator-value
5064;data;/ietf-schc:schc/rule/entry/matching-operator-value/index
5065;data;/ietf-schc:schc/rule/entry/matching-operator-value/value
5066;data;/ietf-schc:schc/rule/entry/target-value
5067;data;/ietf-schc:schc/rule/entry/target-value/index
5068;data;/ietf-schc:schc/rule/entry/target-value/value
5069;data;/ietf-schc:schc/rule/entry
5070;data;/ietf-schc:schc/rule/entry-option-space
5071;data;/ietf-schc:schc/rule/entry-option-space/comp-decomp-action
5072;data;/ietf-schc:schc/rule/entry-option-space/comp-decomp-action-value
5073;data;/ietf-schc:schc/rule/entry-option-space/comp-decomp-action-value/index
5074;data;/ietf-schc:schc/rule/entry-option-space/comp-decomp-action-value/value
5075;data;/ietf-schc:schc/rule/entry-option-space/direction-indicator
5076;data;/ietf-schc:schc/rule/entry-option-space/field-length
5077;data;/ietf-schc:schc/rule/entry-option-space/field-position
5078;data;/ietf-schc:schc/rule/entry-option-space/matching-operator
5079;data;/ietf-schc:schc/rule/entry-option-space/matching-operator-value
5080;data;/ietf-schc:schc/rule/entry-option-space/matching-operator-value/index
5081;data;/ietf-schc:schc/rule/entry-option-space/matching-operator-value/value
5082;data;/ietf-schc:schc/rule/entry-option-space/option-value
5083;data;/ietf-schc:schc/rule/entry-option-space/space-id
5084;data;/ietf-schc:schc/rule/entry-option-space/target-value
5085;data;/ietf-schc:schc/rule/entry-option-space/target-value/index
5086;data;/ietf-schc:schc/rule/entry-option-space/target-value/value
5087;data;/ietf-schc:schc/rule/entry/comp-decomp-action
5088;data;/ietf-schc:schc/rule/entry/comp-decomp-action-value
5089;data;/ietf-schc:schc/rule/entry/comp-decomp-action-value/index
5090;data;/ietf-schc:schc/rule/entry/comp-decomp-action-value/value
5091;data;/ietf-schc:schc/rule/entry/direction-indicator
5092;data;/ietf-schc:schc/rule/entry/field-id
~~~
{: #fig-sid-assignation  title="CBOR serialisation." artwork-align="center"}


## Syntatic compression (Quentin)

with options decomposed with delta Type, Length, Value.

## Revised RFC9363 

with Corentin proposal to flatten the rule entries

## Summary

~~~
  +--------+---------+----------+--------+---------+------------+---------+
  |        | RFC9363 | Univ Opt | merged | ordered |  Syntactic | Revised |
  +--------+---------+==========+========+=========+------------+---------+
  |CORECONF|    357  |     481  |    400 |     376 |            |         |       
  +--------+---------+----------+--------+---------+------------+---------+
  |Query   |     14  |      15  |     15 |      15 |            |         |
  +--------+---------+----------+--------+---------+------------+---------+
  |SCHC pkt|     49  |      49  |     49 |      49 |            |         |
  +--------+---------+----------+--------+---------+------------+---------+

~~~

# Acknowledgments # {#acknowledgments}
{:unnumbered}

The authors sincerely thank

This work was supported by the Sweden's Innovation Agency VINNOVA within the EUREKA CELTIC-NEXT project CYPRESS.
