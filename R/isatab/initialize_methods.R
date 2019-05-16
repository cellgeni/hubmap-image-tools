library( dplyr )

# ISATabInvestigation object.
setMethod( "initialize", "ISATabInvestigation", function( .Object, isatabRisa ) {
    
    #.Object.isatabRisa <- isatabRisa

    .Object@identifier <- isatabRisa@investigation.identifier


    .Object@filename <- file.path( isatabRisa@path, isatabRisa@investigation.filename )
    
    # Convert all columns of the investigation file data frame to character type.
    investigationFile <- isatabRisa@investigation.file %>% mutate_all( as.character )
    
    # Get the main INVESTIGATION section of the file.
    investigationMainSection <- .grab_single_section( "^INVESTIGATION$", investigationFile )

    .Object@comments <- .make_comments( investigationMainSection )
    .Object@title <- .grab_field_contents( investigationMainSection, "Investigation Title" )
    .Object@description <- .grab_field_contents( investigationMainSection, "Investigation Description" )
    .Object@submission_date <- .grab_field_contents( investigationMainSection, "Investigation Submission Date" )
    .Object@public_release_date <- grab_field_contents( investigationMainSection, "Investigation Public Release Date" )

    .Object@ontologies <- .create_section_objects( investigationFile, "ONTOLOGY SOURCE REFERENCE", "ISATabOntology" )
    .Object@publications <- .create_section_objects( investigationFile, "INVESTIGATION PUBLICATIONS", "ISATabPublication" )
    .Object@contacts <- .create_section_objects( investigationFile, "INVESTIGATION CONTACTS", "ISATabContact" )

    studies <- .create_studies( investigationFile, isatabRisa )


    return( .Object )
} )


setMethod( "initialize", "ISATabStudy", function( .Object, studyRows, isatabRisa ) {

    studyMainSection <- .grab_single_section( "^STUDY$", studyRows )

    .Object@filename <- file.path( isatabRisa@path, .grab_field_contents( studyMainSection, "Study File Name" ) )
    .Object@identifier <- .grab_field_contents( studyMainSection, "Study Identifier" )
    .Object@title <- .grab_field_contents( studyMainSection, "Study Title" )
    .Object@description <- .grab_field_contents( studyMainSection, "Study Description" )
    .Object@submission_date <- .grab_field_contents( studyMainSection, "Study Submission Date" )
    .Object@public_release_date <- .grab_field_contents( studyMainSection, "Study Public Release Date" )

    .Object@comments <- .make_comments( studyMainSection )
    
    .Object@contacts <- .create_section_objects( studyRows, "STUDY CONTACTS", "ISATabContact" )
    .Object@publications <- .create_section_objects( studyRows, "STUDY PUBLICATIONS", "ISATabPublication" )
    .Object@factors <- .create_section_objects( studyRows, "STUDY FACTORS", "ISATabFactor" )
    .Object@protocols <- .create_section_objects( studyRows, "STUDY PROTOCOLS", "ISATabProtocol" )
    .Object@design_descriptors <- create_section_objects( studyRows, "STUDY DESIGN DESCRIPTORS", "ISATabStudyDesign" )

    # FIXME: Add the Sample->Assay->File(s) representation.
    .Object@study_assays <- .create_section_objects( studyRows, "STUDY ASSAYS", "ISATabStudyAssay" )

    sources <- .build_study_graph( isatabRisa@study.files[[ .Object@identifier ]] )
    
    return( .Object )
} )


# ISATabOntology object.
setMethod( "initialize", "ISATabOntology", function( .Object, ontologyTable ) {

    .Object@term_source_name <- .grab_field_contents( ontologyTable, "Term Source Name" )
    .Object@term_source_file <- .grab_field_contents( ontologyTable, "Term Source File" )
    .Object@term_source_version <- .grab_field_contents( ontologyTable, "Term Source Version" )
    .Object@term_source_description <- .grab_field_contents( ontologyTable, "Term Source Description" )

    return( .Object )
} )


# ISATabPublication object.
setMethod( "initialize", "ISATabPublication", function( .Object, pubTable ) {

	.Object@pubmed_id <- .grab_field_contents( pubTable , "PubMed ID" )
    .Object@doi <- .grab_field_contents( pubTable, "Publication DOI" )
    .Object@author_list <- .grab_field_contents(pubTable, "Publication Author List" )
    .Object@title <- .grab_field_contents( pubTable, "Publication Title" )
    .Object@status <- .grab_field_contents( pubTable, "Publication Status" )
    .Object@status_term_accession <- .grab_field_contents( pubTable, "Publication Status Term Accession Number" )
    .Object@status_term_source_ref <- .grab_field_contents( pubTable, "Publication Status Term Source REF" )

	return( .Object )
} )


# ISATabContact object.
setMethod( "initialize", "ISATabContact", function( .Object, contactTable ) {

    .Object@last_name <- .grab_field_contents( contactTable, "Person Last Name" )
    .Object@first_name <- .grab_field_contents( contactTable, "Person First Name" )
    .Object@mid_initials <- .grab_field_contents( contactTable, "Person Mid Initials" )
    .Object@email <- .grab_field_contents( contactTable, "Person Email" )
    .Object@phone <- .grab_field_contents( contactTable, "Person Phone" )
    .Object@fax <- .grab_field_contents( contactTable, "Person Fax" )
    .Object@address <- .grab_field_contents( contactTable, "Person Address" )
    .Object@affiliation <- .grab_field_contents( contactTable, "Person Affiliation" )
    .Object@roles <- .grab_field_contents( contactTable, "Person Roles" )
    .Object@roles_term_accession <- .grab_field_contents( contactTable, "Person Roles Term Accession Number" )
    .Object@roles_term_source_ref <- .grab_field_contents( contactTable, "Person Roles Term Source REF" )

    # Comments are different.
    .Object@comments <- .make_comments( contactTable )

    return( .Object )
} )


# ISATabStudyFactor.
setMethod( "initialize", "ISATabStudyFactor", function( .Object, factorTable ) {

    .Object@name <- .grab_field_contents( factorTable, "Study Factor Name" )
    .Object@type <- .grab_field_contents( factorTable, "Study Factor Type" )
    .Object@type_term_accession_number <- .grab_field_contents( factorTable, "Study Factor Type Term Accession Number" )
    .Object@type_term_source_ref <- .grab_field_contents( factorTable, "Study Factor Type Term Source REF" )

    return( .Object )
} )


# ISATabProtocol.
setMethod( "initialize", "ISATabProtocol", function( .Object, protocolTable ) {

    .Object@name <- .grab_field_contents( protocolTable, "Study Protocol Name" )
    .Object@type <- .grab_field_contents( protocolTable, "Study Protocol Type" )
    .Object@type_term_accession_number <- .grab_field_contents( protocolTable, "Study Protocol Type Term Accession Number" )
    .Object@type_term_source_ref <- .grab_field_contents( protocolTable, "Study Protocol Type Term Source REF" )
    .Object@description <- .grab_field_contents( protocolTable, "Study Protocol Description" )
    .Object@uri <- .grab_field_contents( protocolTable, "Study Protocol URI" )
    .Object@version <- .grab_field_contents( protocolTable, "Study Protocol Version" )
    .Object@parameters_name <- .grab_field_contents( protocolTable, "Study Protocol Parameters Name" )
    .Object@parameters_name_term_source_accession_number <- .grab_field_contents( protocolTable, "Study Protocol Name Term Source Accession Number" )
    .Object@parameters_name_term_source_ref <- .grab_field_contents( procotolTable, "Study Protocol Name Term Source REF" )
    .Object@components_name <- .grab_field_contents( protocolTable, "Study Protocol Components Name" )
    .Object@components_type <- .grab_field_contents( protocolTable, "Study Protocol Components Type" )
    .Object@components_type_term_accession_number <- .grab_field_contents( protocolTable, "Study Protocol Components Type Term Accession Number" )
    .Object@components_type_term_source_ref <- .grab_field_contents( protocolTable, "Study Protocol Components Type Term Source REF" )

    return( .Object )
} )


setMethod( "initialize", "ISATabStudyDesign", function( .Object, designTable ) {

    .Object@type <- .grab_field_contents( designTable, "Study Design Type" )
    .Object@type_term_accession_numer <- .grab_field_contents( designTable, "Study Design Type Term Accession Number" )
    .Object@type_term_source_ref <- .grab_field_contents( designTable, "Study Design Type Term Source REF" )

    return( .Object )
} )

