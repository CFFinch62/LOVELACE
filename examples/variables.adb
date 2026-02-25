with Ada.Text_IO; use Ada.Text_IO;
with Ada.Integer_Text_IO; use Ada.Integer_Text_IO;
with Ada.Float_Text_IO; use Ada.Float_Text_IO;

procedure Variables is
   Age    : Integer := 25;
   Height : Float   := 1.75;
   Letter : Character := 'A';
   Is_Ok  : Boolean := True;
begin
   Put("Age: ");
   Put(Age, Width => 0);
   New_Line;
   
   Put("Height: ");
   Put(Height, Fore => 1, Aft => 2, Exp => 0);
   New_Line;
   
   Put_Line("Letter: " & Letter);
   
   if Is_Ok then
      Put_Line("Status: OK");
   end if;
end Variables;
