#include <iostream>

#include "MuSR_td_PSI_bin.h"


int check_bin(MuSR_td_PSI_bin *pexample_test) {
  int ret;

  ret = 0;

  if (pexample_test && pexample_test->readingOK()) {

    pexample_test->Show();

    if (pexample_test->get_numberHisto_int() > 0) {


      cout << "Name of first histogram (of Run # : "
           << pexample_test->get_runNumber_int() << ") : "
           << pexample_test->get_histoNames_vector()[0]
           << endl ;

      cout << "The t_0 is at : "          << pexample_test->get_t0_int(0)
           << " and the first_good at : " << pexample_test->get_firstGood_int(0)
           <<  endl ;
      cout << "The last_good is at : "    << pexample_test->get_lastGood_int(0)
           <<  endl ;
      cout << endl ;

      int it;

      it = pexample_test->get_firstGood_int(0) - pexample_test->get_t0_int(0)+16;
      cout << "The bin # " << it << " after t_0 contains : "
           << pexample_test->get_histo_vector(0,1)[20+pexample_test->get_t0_int(0)]
           << endl ;

      cout << "By subtracting the background between 50 and 100, this bins contains : "
           << pexample_test->get_histo_fromt0_minus_bckgrd_vector(0,50,100,1)[it]
           << endl ;

      cout << "and it correspond to the 16th bin after the first_good : "
           << pexample_test->get_histo_goodBins_minus_bckgrd_vector(0,50,100,1)[16]
           << endl ;

      // change public histo
      cout << "public variable histos_vector[0][0] = "
           << pexample_test->histos_vector[0][0] << endl;
      cout << "Will now be set to 15.2" << endl;
      pexample_test->histos_vector[0][0] = 15.2;
      cout << "histos_vector[0][0] = " << pexample_test->histos_vector[0][0] << endl;

      // does not change private
      cout << "this does not change histo[0][0]" << endl;
      cout << " get_histo(0,0) = "    << pexample_test->get_histo(0,0) << endl;
      cout << " get_histo_int(0,0) = " << pexample_test->get_histo_int(0,0) << endl;

      // remember to delete information returned by * ...._array() methods
      // to free up memory
      int *histo0 = pexample_test->get_histo_array_int(0);

      if (histo0 != NULL) delete [] histo0; histo0 = NULL;


    } else {
      cout << "Number of histograms < 1!" << endl;
      ret = 1;
    }
    cout << "***** " << pexample_test->Filename() << endl << endl;

  } else {
    if (pexample_test == NULL)
      cout << "ERROR NULL pointer to MuSR_td_PSI_bin!" << endl;
    else if (!pexample_test->readingOK()) {
      cout << "ERROR Reading of file " << pexample_test->Filename() << " failed!"
           << endl;
      cout << "***** " << pexample_test->ReadStatus() << " ******" << endl;
    }
    ret = 1;
  }
  return ret;
}

int main( int argc, char ** argv )

  {
    MuSR_td_PSI_bin example_test ;

    example_test.read("deltat_pta_gps_0001.bin") ;
    check_bin(&example_test);

    example_test.read("pta_gps_2008_07387_14.mdu") ;
    check_bin(&example_test);

  }

