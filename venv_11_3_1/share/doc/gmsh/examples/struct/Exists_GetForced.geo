//
// Functions: Exists(.) and GetForced(.)
//   (for both Gmsh and GetDP)
//

val_real = 12;

list_of_real() = {11 ,22, 33};

Struct namespace::struct_name [ Dim 2, Ref 5 ]; // See file struct.geo for Struct definitions

// Look at the Current Workspace for checking the variables contents.

//
// Function Exists(name_variable):
//   returns 1 if variable 'name_variable' exists, 0 if not

If (Exists(val_real))
  Printf("Variable 'val_real' exists");
EndIf

If (!Exists(other_val_real))
  Printf("Variable 'other_val_real' does not exist");
EndIf

If (Exists(list_of_real))
  Printf("List 'list_of_real()' exists");
EndIf

If (Exists(namespace::struct_name.Dim))
  Printf("Member 'Dim' of structure 'namespace::struct_name' exists");
EndIf

If (!Exists(namespace::struct_name.Thickness))
  Printf("Member 'Thickness' of structure 'namespace::struct_name' does not exist");
  Struct namespace::struct_name (Append) [ Thickness 0.01 ]; // This member is added to the structure
  If (Exists(namespace::struct_name.Thickness))
    Printf("Member 'Thickness' of structure 'namespace::struct_name' now exists");
  EndIf
EndIf

//
// GetForced(name_variable, default_value):
//   returns value of 'name_variable' if it exists, default_value if not
// GetForced(name_variable):
//   returns value of 'name_variable' if it exists, 0 (zero) if not
// (name_variable can be an element of a list)

get_forced_val_real = GetForced(val_real, 1); // Will be 12, the value of the existing  variable

get_forced_other_val_real_with_defined_default_value = GetForced(other_val_real, 1); // Will be 1 (defined default value) because variable does not exist
get_forced_other_val_real_with_zero_default_value = GetForced(other_val_real); // Will be 0 (default value) because variable does not exist

get_forced_struct_member_with_default = GetForced(namespace::struct_name.InexistingMember, -1); // Will be the defined default value -1

get_forced_out_of_range_element_of_list_of_real_with_defined_default_value = GetForced(list_of_real(99), 1); // Will be 1 (defined default value) because element of list does not exist (out of range)

get_forced_element_of_other_list_of_real_with_defined_default_value = GetForced(other_list_of_real(0), 1); // Will be 1 (defined default value) because list does not exist

// GetForced also applies for list members of a structure
Struct struct_with_list_member [ list_member {111,222,333}];
get_forced_inexistent_element_of_member_list_of_real = GetForced(struct_with_list_member.list_member(99), -1); // Will give default value -1

//
