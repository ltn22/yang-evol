---
v: 3

title: Options representation in SCHC YANG Data Models
abbrev: SCHC for CoAP
docname: draft-toutain-schc-universal-option

area: Internet
wg: SCHC Working Group
kw: Internet-Draft
cat: std
submissiontype: IETF

coding: utf-8

author:
      -
        ins: A. Minaburo
        name: Ana Minaburo
        org: Consultant
        street: Rue de Rennes
        city: Cesson-Sevigne
        code: 35510
        country: France
        email: anaminaburo@gmail.com
      -
        ins: M. Tiloca
        name: Marco Tiloca
        org: RISE AB
        street: Isafjordsgatan 22
        city: Kista
        code: SE-16440
        country: Sweden
        email: marco.tiloca@ri.se
      -
        ins: L. Toutain
        name: Laurent Toutain
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

entity:
  SELF: "[RFC-XXXX]"

--- abstract

The idea of keeping option identifiers  in SCHC Rules simplifies the interoperability and the evolution of SCHC compression, when the protocol introduces new options, that can be unknown from the current SCHC implementation. This document discuss the augmentation of the current YANG Data Model, in order to add in the Rule options identifiers used by the protocol. 


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

~~~~~~~~~~~

<CODE BEGINS> file "ietf-schc-opt@2024-12-19.yang"


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

<CODE ENDS>
~~~


# Acknowledgments # {#acknowledgments}
{:unnumbered}

The authors sincerely thank 