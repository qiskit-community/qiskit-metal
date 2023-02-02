//
// DATA STRUCTURES (for both Gmsh and GetDP)
//

// A data structure is a group of data elements grouped together under one name,
// the structure identifier. These data elements, defining the structure members,
// can be of different types: real, string, list of real, list of string.
// The syntax should be clear from the example below:

Struct struct_identifier [
  struct_member_real_1 11.,
  struct_member_real_2 22.,
  struct_member_string_1 "string1",
  struct_member_string_2 "string2",
  struct_member_list_of_real_1 { 111., 222., 333. },
  struct_member_list_of_string_1 Str[ {"string_l_1", "string_l_2"} ]
];

// Look at the Current Workspace for checking the structure content.
// You will see there that a structure is automatically given a (real) 'Tag' member,
// starting at 1 and incremented by 1 for each new structure.
// When given in an RHS expression, the Struct definition returns its 'Tag',
// that can also be explicitly given:

Struct St1 [ Type 1 ]; // Tag will be 2 = 1 (the one of last Struct) + 1
Struct St2 [ Type 2, Tag 10 ]; // Tag is forced to 10
tag_of_struct_St3 = Struct St3 [ Type 3 ]; // Tag will be 11 = 10 + 1

// For clear classifications (contexts), structures can be defined in
// namespaces (other than the global one used until now).
// Their names then start with the namespace name followed by the
// scope operator '::'. The 'Tag' numbering is proper to each namespace. E.g.,

Struct NS1::St1 [ Type 1 ]; // Tag will be 1 (for the 1st structure in namespace 'NS1')
Struct NS1::St2 [ Type 2 ];
Struct NS1::St3 [ Type 3 ];

// To access the value of a member of a structure, use the dot '.' operator
// between the structure name (with possible namespace) and the member name:

val_Type_of_Struct_St2 = St2.Type;
val_Type_of_Struct_St2_in_NS1 = NS1::St2.Type;

// To access a 'Tag': via the Tag member or directly with the single structure name
// (with possible namespace)

tag_of_struct_St1 = St1.Tag;
tag_of_struct_NS1_St1 = NS1::St1.Tag;

direct_tag_of_struct_St1 = St1;
direct_tag_of_struct_NS1_St1 = NS1::St1;

// To access real list members:
one_element_from_a_list_member = struct_identifier.struct_member_list_of_real_1(1);
full_list_from_a_list_member() = struct_identifier.struct_member_list_of_real_1();
dim_list_member = #struct_identifier.struct_member_list_of_real_1();

// To access string list members:
one_string_from_a_list_member = Str[struct_identifier.struct_member_list_of_string_1(1)];
full_string_list_from_a_list_member() = Str[struct_identifier.struct_member_list_of_string_1()];
dim_string_list_member = #struct_identifier.struct_member_list_of_string_1();

// Function DimNameSpace(.) returns the number of structures in a given namespace:

nb_struct_namespace_global = DimNameSpace();
nb_struct_namespace_NS1 = DimNameSpace(NS1);

// Function NameStruct(namespace::#index)
// (or NameStruct(#index) for the global namespace)
// returns the name (as a string) of the index-th structures in the given namespace:

name_of_struct_2_in_namespace_global = NameStruct(#2);
name_of_struct_2_in_namespace_NS1 = NameStruct[NS1::#2];

// Thanks to these two functions, and function S2N[.] ('StringToName'),
// one can make loops on structures of a given namespace and
// access their members values:

For i In {1:DimNameSpace(NS1)}
  id_NS1~{i} = NameStruct[NS1::#i]; // Gets the identifier of the i-th structure in NS1
  val_Type_of_NS1_struct~{i} = NS1::S2N[id_NS1~{i}].Type; // Gets the value of member Type
  // Prints all that
  Printf(Sprintf[StrCat["id of %g-th structure in NS1 = '", id_NS1~{i}, "'"], i]);
  Printf("Value of member 'Type' of %g-th structure in NS1 = %g",
         i, val_Type_of_NS1_struct~{i});
EndFor

// Some additional members can be appended to an existing structure,
// with '(Append)' following the structure name:

Struct NS1::St2 (Append) [ AdditionalMember 222 ];
Struct NS1::St3 (Append) [ AdditionalMember 333, HColor "Orange" ];

// STRUCT FOR ENUMERATIONS
// A structure can be used to define an enumeration, to give automatically
// incremented values to the members (by default, starting at 0, or at any fixed value).
// This is useful, e.g., for defining constants to be used for types (hidding the values):

Struct T::REGION_TYPE [ Enum, NONE, PHYS, SKIN, GATE, BC ];
// Automatic values will be: NONE 0, PHYS 1, SKIN 2, GATE 3, BC 4

Struct T::REGION_TYPE_2 [ Enum, PHYS 10, SKIN, GATE 20, BC ];
// Automatic values will be: PHYS 10, SKIN 11, GATE 20, BC 21

// To add members with Append:
Struct T::REGION_TYPE (Append) [ Enum, CUTBOX ]; // CUTBOX will be 5

// Using explicit name for constants:
myType = T::REGION_TYPE.PHYS;
If (myType == T::REGION_TYPE.PHYS)
  // ...
EndIf


// You can now play with all that!
//
