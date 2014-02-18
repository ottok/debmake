# Fake download session
export URL=http://search.cpan.org/CPAN/authors/id/M/MG/MGRABNAR/File-Tail-0.99.3.tar.gz
echo "File-Tail-0.99.3" >${BASEDIR}/project
L "wget $URL"
