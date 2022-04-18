

## TRIUMF
Sadly, no one has made a python package wrapping Triumf's C library (though I am sorely tempted to at this point) so we do still need to work with it. Good news is, they very rarely change it so we should be good, or at the very least only need to make very minor changes.

## PSI
We used to use PSI's [C++ class](http://lmu.web.psi.ch/docu/manuals/bulk_manuals/software/Class_MuSR_PSI/index.html) to read in .bin and .mdu files but I found a python package which acted as a wrapper and was much easier to work with on our end since we didn't need to compile and run executables.

## ISIS
Similiar to PSI we used to use a Java library for HDF5 to read in the nxs_v2 files but turns out, once again, someone made a python library for that. So we are using it instead.
