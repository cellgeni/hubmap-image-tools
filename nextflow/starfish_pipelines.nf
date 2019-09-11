#!/usr/bin/env nextflow

// Output filename(s) FIXME: put these in a config file.
dartfish_results_file_in = Channel.fromPath( params.dartfishOutfile )
seqfish_results_file_in = Channel.fromPath( params.seqfishOutfile )

process run_starfish_dartfish {

    publishDir "$PWD"

    input:
        val outfile from dartfish_results_file_in

    output:
        file "*.txt" into starfish_dartfish_results
        stdout starfish_dartfish_stdout

    """
    python3 $HUBMAP_IMAGE_TOOLS/python/starfish/dartfish.py -o ${outfile}
    """
}


process run_starfish_seqfish {

    publishDir = "$PWD"

    input: 
        val outfile from seqfish_results_file_in

    output:
        file "*.txt" into starfish_seqfish_results
    
    """
    python3 $HUBMAP_IMAGE_TOOLS/python/starfish/seqfish.py -o ${outfile}
    """
}

