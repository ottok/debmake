# Fake download session
export URL=http://search.cpan.org/CPAN/authors/id/A/AU/AUDREYT/Acme-Hello-0.05.tar.gz
echo "Acme-Hello-0.05" >${BASEDIR}/project
L "wget $URL"
