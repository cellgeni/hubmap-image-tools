# ISATabComponent class.
setClass(
    "ISATabComponent",
    slots = c(
        filename = "character",
        identifier = "character",
        title = "character",
        description = "character",
        submission_date = "character",
        public_release_date = "character",
        contacts = "SimpleList",
        comments = "SimpleList",
        publications = "SimpleList"
    )
)


# ISATab Investigation class.
setClass( 
    "ISATabInvestigation", 
    contains = "ISATabComponent",
    slots = c(
        ontologies = "SimpleList",
        studies = "SimpleList"
    )
)

# Study class.
setClass(
    "ISATabStudy",
    contains = "ISATabComponent",
    slots = c(
        study_assays = "SimpleList",
        design_descriptors = "SimpleList",
        factors = "SimpleList",
        protocols = "SimpleList",
        sources = "SimpleList",
        samples = "SimpleList"
    )
)

# Ontology class.
setClass(
    "ISATabOntology",
    slots = c(
        term_source_name = "character",
        term_source_file = "character",
        term_source_version = "character",
        term_source_description = "character"
    )
)


setClass(
	"ISATabPublication",
	slots = c(
		pubmed_id = "character",
		doi = "character",
        author_list = "character",
        title = "character",
        status = "character",
        status_term_accession = "character",
        status_term_source_ref = "character" # this has to be in the investigation ontologies.
    )
)


setClass(
    "ISATabContact",
    slots = c(
        last_name = "character",
        first_name = "character",
        mid_initials = "character",
        email = "character",
        phone = "character",
        fax = "character",
        address = "character",
        affiliation = "character",
        roles = "character",
        roles_term_accession = "character",
        roles_term_source_ref = "character",
        comments = "SimpleList"
    )
)


setClass(
    "ISATabComment",
    slots = c(
        name = "character",
        value = "character"
    )
)

setClass(
    "ISATabStudyFactor",
    slots = c(
        name = "character",
        type = "character",
        type_term_accession_number = "character",
        type_term_source_ref = "character"
    )
)

setClass(
    "ISATabProtocol",
    slots = c(
        name = "character",
        type = "character",
        type_term_accession_number = "character",
        type_term_source_ref = "character",
        description = "character",
        uri = "character",
        version = "character",
        parameters_name = "character",
        parameters_name_term_accession_number = "character",
        parameters_name_term_source_ref = "character",
        components_name = "character",
        components_type = "character",
        components_type_term_accession_number = "character",
        components_type_term_source_ref = "character"
    )
)


setClass(
    "ISATabStudyDesign",
    slots = c(
        type = "character",
        type_term_accession_number = "character",
        type_term_source_ref = "character"
    )
)


setClass(
    "ISATabNode",
    slots = c(
        row_indices = "vector"
    )
)


setClass(
    "ISATabMaterial",
    contains = "ISATabNode",
    slots = c(
        input_process_nodes = "SimpleList",
        output_process_nodes = "SimpleList",
        name = "character",
        characteristics = "SimpleList"
    )
)


setClass(
    "ISATabBioSource",
    contains = "ISATabMaterial"
)


setClass(
    "ISATabSample",
    contains = "ISATabMaterial"
)


setClass(
   "ISATabUnit",
   slots = c(
       type = "character",
       value = "character"
   )
)


setClass(
    "ISATabCharacteristic",
    slots = c(
        type = "character",
        value = "character",
        unit = "ISATabUnit"
    )
)


setClass(
    "ISATabProcessNode",
    contains = "ISATabNode",
    slots = c(
        protocol_ref = "character",
        input_material_nodes = "SimpleList",
        output_material_nodes = "SimpleList"
    )
)
