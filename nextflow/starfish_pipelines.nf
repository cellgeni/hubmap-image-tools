#!/usr/bin/env nextflow

def inputFileList = new File( "starfish_input_files.json" )

// Output filename(s) from config file
// (hubmap-image-tools/nextflow/starfish_nextflow.config ; copy to working dir
// and rename to nextflow.config).
// FIXME: Final pipeline should have input file(s) instead of output files but
// for now we are using Starfish example data to test with.
//dartfish_results_file_in = Channel.from( params.dartfishOutfile )
//seqfish_results_file_in = Channel.from( params.seqfishOutfile )

// Try and do this with a JSON config instead.
import groovy.json.JsonSlurper
def jsonSlurper = new JsonSlurper()

String inputFilesJSON = inputFileList.text
def inputFiles = jsonSlurper.parseText( inputFilesJSON )

dartfish_results_file_in = Channel.from( inputFiles.dartfish_outfiles )
seqfish_results_file_in = Channel.from( inputFiles.seqfish_outfiles )

process run_starfish_dartfish {

    publishDir "$PWD"

    input:
        val outfile from dartfish_results_file_in

    output:
        file "*.txt" into starfish_dartfish_results

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

