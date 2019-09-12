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

List dartfishOutfiles = inputFiles.dartfish_outfiles
List seqfishOutfiles = inputFiles.seqfish_outfiles

if( dartfishOutfiles ) {
    
    numFiles = dartfishOutfiles.size()
    println "Found $numFiles DARTFISH file(s) to process."
    
    dartfish_results_file_in = Channel.from( inputFiles.dartfish_outfiles )

} else {

    dartfish_results_file_in = Channel.from( "NOFILES" )
    
    println "No DARTFISH files to process."
}

if( seqfishOutfiles ) {
    
    numFiles = seqfishOutfiles.size()
    println "Found $numFiles seqFISH file(s) to process."
    
    seqfish_results_file_in = Channel.from( inputFiles.seqfish_outfiles )

} else {
    
    seqfish_results_file_in = Channel.from( "NOFILES" )
    
    println "No seqFISH files to process."
}


process run_starfish_dartfish {

    publishDir "$PWD"

    input:
        val outfile from dartfish_results_file_in

    output:
        file "*.txt" into starfish_dartfish_results

    when:
        outfile != "NOFILES"

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

    when:
        outfile != "NOFILES"
    
    """
    python3 $HUBMAP_IMAGE_TOOLS/python/starfish/seqfish.py -o ${outfile}
    """
}

