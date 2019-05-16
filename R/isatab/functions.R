
#create_isatab_investigation <- function( isatabDirectory ) {

#    suppressMessages( library( Risa ) )

#    isatabRisa <- readISATab( path = isatabDirectory )



#.create_studies <- function( investigationFile ) {

library( S4Vectors )

.create_section_objects <- function( sectionFile, tagName, className ) {

    sectionRows <- .select_section_rows( sectionFile, tagName )
    
    # If we just got one-column data frame(s) back, there is no info for this section.
    if( all( sapply( sectionRows, function( x ) ncol( x ) == 1 ) ) ) {
        return( NULL )
    }

    objects <- c( sapply( sectionRows, function( rows ) {

        sapply( 2:ncol( rows ), function( i ) {

            object <- new( className, rows[ , c( 1, i ) ] )
        } )
    } ) )

    return( SimpleList( objects ) )
}


.create_studies <- function( investigationFile ) {

    allStudyRows <- .select_section_rows( investigationFile, "STUDY" )
    
    allStudies <- sapply( allStudyRows, function( studyRows ) {

        new( "ISATabStudy", studyRows )
    } )

    return( SimpleList( allStudies ) )
}


.grab_single_section <- function( sectionHeaderPattern, fileRows ) {

    sectionHeaderRowIndex <- grep( sectionHeaderPattern, fileRows[ , 1 ] )
    
    i <- sectionHeaderRowIndex + 1

    tag <- investigationFile[ i, 1 ]

    while( grepl( "[a-z]", tag ) ) {

        tag <- fileRows[ i, 1 ]

        i <- i + 1
    }

    return( fileRows[ ( sectionHeaderRowIndex + 1 ):( i - 2 ), ] )
}


.select_section_rows <- function( fileRows, sectionName ) {
    
    sectionHeaderPattern <- paste( "^", sectionName, "$", sep = "" )

    sectionHeaderRowIndices <- grep( 
        sectionHeaderPattern,
        fileRows[ , 1 ]
    )

    sectionRows <- lapply( sectionHeaderRowIndices, function( i ) {

        j <- i + 1
        
        tag <- fileRows[ j, 1 ]
        
        while( !grepl( sectionHeaderPattern, tag ) && j-1 <= nrow( fileRows ) ) {
        
            if( !grepl( "[a-z]", tag ) && !grepl( paste( "^", sectionName, sep = "" ), tag ) ) {
                break
            }
            
            tag <- fileRows[ j , 1 ]
            
            j <- j + 1
        }

        fileRows <- fileRows[ (i+1):(j-2), ]
        
        # Remove empty columns.
        fileRows <- fileRows[ !sapply(fileRows, function(x) all(x == "")) ]

        # Various sections could be either from Investigation or
        # Study -- to make it generic, remove the word "Investigation" or Study
        # from the beginning of the first column values.
        fileRows[ , 1 ] <- gsub( "Investigation |Study ", "", fileRows[ , 1 ] )

        fileRows
    })

    return( sectionRows )
}


.grab_field_contents <- function( sectionTable, fieldName ) {

    return( sectionTable[ which( sectionTable[ , 1 ] == fieldName ), 2 ] )
}


.make_comments <- function( sectionTable ) {
    
    if( ncol( sectionTable ) > 2 ) {
        
        stop( 
            paste( 
                "ERROR: trying to make ISATabComments with more than two columns of data, this is invalid."
            )
        )
    }

    commentRows <- sectionTable[ grep( "^Comment\\s*\\[", sectionTable[ , 1 ] ) , ]

    commentNames <- apply( commentRows, 1, function( commentRow ) {
        gsub( "^Comment\\s*\\[(.*)\\]$", "\\1", commentRow[ 1 ] )
    } )
    
    names( commentNames ) <- NULL

    comments <- sapply( 1:nrow( commentRows ), function( i ) {
        comment <- new( "ISATabComment", name = commentNames[ i ], value = commentRows[ i , 2 ] )
    } )
    
    return( SimpleList( comments ) )
}


.build_study_graph <- function( studyTable ) {

    sourceNames <- unique( studyTable[[ "Source Name" ]] )

    sources <- sapply( sourceNames, function( sourceName ) {
        
        # Get the row indices for this biosource.
        sourceRowIndices <- which( studyTable[[ "Source Name" ]] == sourceName )

        # The column index should always be 1, but "just in case"...
        sourceColIndex <- which( colnames( studyTable ) == "Source Name" )

        i <- sourceColIndex + 1

        colName <- colnames( studyTable )[ i ]

        while( !grepl( "^Protocol REF$", colName ) ) {

            colName <- colnames( studyTable )[ i ]

            i <- i +1
        }

        # All columns/rows for this biosource, stopping at and excluding the
        # Protocol REF column(s).
        sourceCols <- studyTable[ sourceRowIndices, sourceColIndex:( i - 1 ) ]
        
        # After removing duplicates there should only be one row.
        if( nrow( sourceCols[ !duplicated( sourceCols ), ] ) > 1 ) { 
            stop( paste( "ERROR: More than one unique row in study file for bio Source", sourceName ) )
        }

        charColIndices <- grep( "^Characteristics\\s*\\[", colnames( sourceCols ) )
        
        charList <- list()

        for( i in 1:length( charColIndices ) ) {
            
            charColIndex <- charColIndices[ i ]
            
            charType <- gsub( "Characteristics\\s*\\[(.*)\\s*\\]$", "\\1", colnames( sourceCols )[ charColIndex ] )
            
            charValue <- sourceCols[ 1, charColIndex ]
            
            characteristic <- new( "ISATabCharacteristic", type = charType, value = as.character( charValue ) )

            nextColIndex <- charColIndex + 1
            
            if( grepl( "^Unit\\s*\\[", colnames( sourceCols )[ nextColIndex ] ) ) {
                unitType <- gsub( "^Unit\\s*\\[\\s*(.*)\\s*\\]$", "\\1", colnames( sourceCols )[ nextColIndex ] )
                unitValue <- sourceCols[ 1, nextColIndex ]
                
                unit <- new( "ISATabUnit", type = unitType, value = unitValue )
                characteristic@unit <- unit
            }

            charList <- append( charList, characteristic )
        }

        sourceNode <- new( 
            "ISATabBioSource", 
            row_indices = sourceRowIndices,
            name = sourceName,
            characteristics = SimpleList( charList )
        )
        
        
        # Now we need to get all the protocols for this biosource.
        #protocolRefColIndices <- grep( "^Protocol REF$", colnames( sourceCols ) )

        #processNodes <- SimpleList()

        #for( i in protocolRefColIndices ) {

        #    processNode <- new( 
        #        "ISATabProcessNode",
        #        protocol_ref = sourceCol[ 1, i ],
        #        input_material_nodes = SimpleList( sourceNode )
        #    )
        #    
        #    append( processNodes, processNode )
        #}
        #
        #sourceNode@output_process_nodes = processNodes
        
        
    } )

    return( sources )
}
