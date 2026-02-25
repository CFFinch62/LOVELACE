with Ada.Text_IO; use Ada.Text_IO;
with Ada.Integer_Text_IO; use Ada.Integer_Text_IO;

procedure Conditionals is
   Score : Integer := 85;
begin
   Put("Score is ");
   Put(Score, Width => 0);
   New_Line;

   -- If / Elsif / Else
   if Score >= 90 then
      Put_Line("Grade: A");
   elsif Score >= 80 then
      Put_Line("Grade: B");
   elsif Score >= 70 then
      Put_Line("Grade: C");
   else
      Put_Line("Grade: F");
   end if;

   -- Case statement
   case Score is
      when 90 .. 100 =>
         Put_Line("Excellent!");
      when 80 .. 89 =>
         Put_Line("Well done!");
      when 70 .. 79 =>
         Put_Line("Good.");
      when others =>
         Put_Line("Needs improvement.");
   end case;
end Conditionals;
