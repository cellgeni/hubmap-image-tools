#!/usr/bin/env perl

=pod

=head1 NAME

fix_ims_header.pl

=head1 SYNOPSIS

fix_ims_header.pl file_with_molecule_names_in_header.csv file_without_molecule_names_in_header.csv

=head1 DESCRIPTION

Some of the CSV sample data from Vanderbilt has the m/z values plus the
molecule names in the column headings. This isn't really needed because they
have also provided a separate CSV containing metadata, which maps m/z values
to their respective molecules. It also makes the data a bit harder to load
into R. This script will convert the header to m/z value only.

=cut

use strict;
use warnings;
use 5.10.0;

use Pod::Usage;

my ( $infile, $outfile ) = @ARGV;

unless( $infile && $outfile ) {
    pod2usage(
        -exitval    => 255,
        -output     => ">&STDOUT",
        -verbose    => 1
    );
}

open my $inFH, "<", $infile or die "Cannot open $infile: $!\n";

open my $outFH, ">", $outfile or die "Cannot open $outfile: $!\n";

while( my $line = <$inFH> ) {

    chomp $line;

    if( $. == 1 ) {

        my @header = split( ",", $line );

        my @newColHeaders = ();

        foreach my $colHeader ( @header ) {
            
            # Format of column heading is e.g.:
            # "m/z 616.4711_CerP(d34:1)-H"
            # The "616.4711" is the m/z value; the section after the "_" is the
            # molecule name.
            ( my $newColHeader = $colHeader ) =~ s/^m\/?z ?_?(\d+\.\d+).*$/$1/;
            
            push @newColHeaders, $newColHeader;
        }
        
        say $outFH join( ",", @newColHeaders );
    }
    else {
        say $outFH $line;
    }
}

$_->close for $inFH, $outFH;

