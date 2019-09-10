#!/usr/bin/env nextflow

// Output filename(s) FIXME: put these in a config file.
dartfish_results_files_in = Channel.from( "nextflow_dartfish_results.txt" )

process run_starfish_dartfish {

    publishDir "$PWD"

    input:
        val outfile from dartfish_results_files_in

    output:
        file "*.txt" into starfish_dartfish_results
        stdout starfish_dartfish_stdout

    """
    python3 $HUBMAP_IMAGE_TOOLS/python/starfish/dartfish.py -o ${outfile} 2>&1
    """
}

starfish_dartfish_stdout.subscribe {
    println it.trim()
}
