with Ada.Text_IO; 
with Ada.Integer_Text_IO;

procedure Loops is
begin
   Ada.Text_IO.Put_Line ("Counting from 1 to 5:");
   for I in 1 .. 5 loop
      Ada.Integer_Text_IO.Put (I);
      Ada.Text_IO.New_Line;
   end loop;
end Loops;
