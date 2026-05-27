#!/usr/bin/php
<?php
ini_set('display_errors', 0);
ini_set('display_startup_errors', 0);
ini_set("error_reporting", E_ALL);
error_reporting(-1);

if(PHP_SAPI != 'cli') {
    echo "Cannot run from browser";
    exit(1);
}

define('JS_TAG', '##JAVASCRIPT##');

$html_template_file = __DIR__.'/template.html';
$output_html_file = __DIR__.'/index2.html';
$js_files = [
    'gps-logger.js',
    'wifi-scanner.js',
    'main.js'
];

$combined_javascript = '';
foreach ($js_files as $file) {
    $file = 'js/'.$file;
    if (is_file($file)) {
        $combined_javascript .= "\n".file_get_contents($file)."\n";
    } else {
        echo "File not found: $file\n";
    }
}
// echo "Combined JS: $combined_javascript\n";

// 2. Write to a temporary workspace file
$tmp_js_file = __DIR__ . '/_combined_workspace.tmp.js';
file_put_contents($tmp_js_file, $combined_javascript);

// 3. Run terser against the file and capture the standard output (stdout)
// Using shell_exec captures whatever the command prints out
// $command = "/usr/bin/terser " . escapeshellarg($tmp_js_file) . " --mangle 2>&1";
$command = "/usr/bin/terser " . escapeshellarg($tmp_js_file) . " 2>&1";
$minified_js = shell_exec($command);
// echo "Minified JS: $minified_js\n";

// 4. Housekeeping: Delete the temporary file right away
if (is_file($tmp_js_file)) {
    unlink($tmp_js_file);
}

$script_wrapper = "<script>\n" . trim('' . $minified_js) . "\n</script>";
$html = file_get_contents($html_template_file);
$html = str_replace(JS_TAG, $script_wrapper, $html);
file_put_contents($output_html_file, $html);

echo "Builder PHP finished creating $output_html_file\n";

function compress_javascript_files($js_files = []) {
    $rv = [];
    if (is_array($js_files)) {
        foreach ($js_files as $file) {
            if (is_file($file)) {
                $new_file = $file . '.min';
                $command = "/usr/bin/terser $file -o $new_file";
                system($command);
                $rv[] = $new_file;
            }
        }
    }
    return $rv;
}

function create_minified_javascript($js_min_files) {
    $rv = '';
    foreach ($js_min_files as $file) {
        $rv .= file_get_contents($file)."\n";
    }
    return trim(''.$rv);
}
?>
