cp -f ../../debian/libkkc2.symbols debian/libkkc2.symbols
echo " \$ vim debian/libkkc2.symbols"
echo " ... (:%s/-1$//)"
echo " ... (:wq)"
L "cat debian/libkkc2.symbols"
