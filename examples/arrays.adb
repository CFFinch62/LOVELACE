with Ada.Text_IO; use Ada.Text_IO;
with Ada.Integer_Text_IO; use Ada.Integer_Text_IO;

procedure Arrays is
   -- Define an array type
   type Integer_Array is array (1 .. 5) of Integer;
   
   -- Declare an array variable and initialize it
   Numbers : Integer_Array := (10, 20, 30, 40, 50);
   Sum     : Integer := 0;
begin
   Put_Line("Array contents:");
   for I in Numbers'Range loop
      Put("Element ");
      Put(I, Width => 0);
      Put(": ");
      Put(Numbers(I), Width => 0);
      New_Line;
      
      Sum := Sum + Numbers(I);
   end loop;
   
   Put("Total sum: ");
   Put(Sum, Width => 0);
   New_Line;
end Arrays;
