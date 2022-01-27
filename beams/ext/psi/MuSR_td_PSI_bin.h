/**************************************************************************************

  MuSR_td_PSI_bin.h

  declaration file of the class 'MuSR_td_PSI_bin'

  Main class to read mdu and td_bin PSI MuSR data.

***************************************************************************************

    begin                : Alex Amato, October 2005
    modified             : Andrea Raselli, October 2009
    copyright            : (C) 2005 by
    email                : alex.amato@psi.ch

***************************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/



#ifndef MuSR_td_PSI_bin_H_
#define MuSR_td_PSI_bin_H_

#include <iostream>
using namespace std ;
#include <fstream>
#include <cstring>
#include <cmath>
#include <string>
#include <vector>

/* ------------------------------------------------------------------ */

const int MAXHISTO     = 32;  // maximum number of histos to process/store
const int MAXSCALER    = 32;  // maximum number of scalers to proces/store
const int MAXTEMPER    =  4;  // maximum number of average temperatures

const int MAXLABELSIZE = 12;  // maximum size of labels

/* ------------------------------------------------------------------ */

class MuSR_td_PSI_bin {

  public:
    MuSR_td_PSI_bin();
   ~MuSR_td_PSI_bin();

  private:
// ------------------------------------start of the variables

    string   filename;
    string   readstatus;
    bool     readingok;

    char     format_id[3] ;

    int      num_run ;

    char     sample[11] ;
    char     temp[11] ;
    char     field[11] ;
    char     orient[11] ;
    char     comment[63] ;

    char     date_start[10] ;
    char     date_stop[10] ;
    char     time_start[9] ;
    char     time_stop[9] ;

    float    bin_width ;

    int      number_histo ;
    int      length_histo ;
    char     labels_histo[MAXHISTO][MAXLABELSIZE] ;

    int      total_events ;
    int      events_per_histo[MAXHISTO] ;

    int      default_binning ;

    float    real_t0[MAXHISTO] ;
    int      integer_t0[MAXHISTO] ;
    int      first_good[MAXHISTO] ;
    int      last_good[MAXHISTO] ;

    int      number_scaler ;
    int      scalers[MAXSCALER] ;
    char     labels_scalers[MAXSCALER][MAXLABELSIZE] ;

    int      number_temper ;
    float    temper[MAXTEMPER] ;
    float    temp_deviation[MAXTEMPER] ;

    int      **histo ;

  public:

/*!< this public variable provides a direct read/write access to the histograms.
     However all public methods use the protected variable histo.
     Histogram information returned by ..._vector or ..._array methods return
     information based on histo bin .

     NOTE: Histogram information returned by \<pointer_to_array\> = ..._array() methods
           should be freed by  delete [] \<pointer_to_array\>;
 */
    vector< vector<double> >  histos_vector ;

// ------------------------------------end of the variables

  public:

    int            read(const char* fileName);      // generic read

    int            readbin(const char* fileName);   // read MuSR PSI bin format
    int            readmdu(const char* fileName);   // read MuSR mdu format

    bool           readingOK()     const;
    string         ReadStatus()    const;
    string         Filename()      const;

    int            Show()          const;
    int            Clear();

    int             get_histo_int(int histo_num, int j);
    double          get_histo(int histo_num, int j);

    int            *get_histo_array_int(int histo_num);
    double         *get_histo_array(int histo_num , int binning) ;
    vector<double>  get_histo_vector(int histo_num , int binning) ;
    vector<double>  get_histo_vector_no0(int histo_num , int binning) ;

    double         *get_histo_fromt0_array(int histo_num ,
                                           int binning ,
                                           int offset = 0) ;

    vector<double>  get_histo_fromt0_vector(int histo_num ,
                                            int binning ,
                                            int offset = 0) ;

    double         *get_histo_goodBins_array(int histo_num , int binning) ;

    vector<double>  get_histo_goodBins_vector(int histo_num , int binning) ;

    double         *get_histo_fromt0_minus_bckgrd_array(int histo_num ,
                                                         int lower_bckgdr ,
                                                         int higher_bckgdr ,
                                                         int binning ,
                                                         int offset = 0) ;

    vector<double>  get_histo_fromt0_minus_bckgrd_vector(int histo_num ,
                                                          int lower_bckgdr ,
                                                          int higher_bckgdr ,
                                                          int binning ,
                                                          int offset = 0) ;

    double         *get_histo_goodBins_minus_bckgrd_array(int histo_num ,
                                                          int lower_bckgrd ,
                                                          int higher_bckgrd ,
                                                          int binning) ;

   vector<double>   get_histo_goodBins_minus_bckgrd_vector(int histo_num ,
                                                           int lower_bckgrd ,
                                                           int higher_bckgrd ,
                                                           int binning) ;

    double         *get_asymmetry_array(int histo_num_plus,
                                         int histo_num_minus,
                                         double alpha_param,
                                         int binning,
                                         int lower_bckgrd_plus,
                                         int higher_bckgrd_plus,
                                         int lower_bckgrd_minus,
                                         int higher_bckgrd_minus ,
                                         int offset = 0,
                                         double y_offset = 0.) ;

    vector<double>  get_asymmetry_vector(int histo_num_plus ,
                                          int histo_num_minus ,
                                          double alpha_param ,
                                          int binning ,
                                          int lower_bckgrd_plus ,
                                          int higher_bckgrd_plus ,
                                          int lower_bckgrd_minus ,
                                          int higher_bckgrd_minus ,
                                          int offset = 0 ,
                                          double y_offset = 0.) ;

    double          *get_error_asymmetry_array(int histo_num_plus ,
                                                int histo_num_minus ,
                                                double alpha_param ,
                                                int binning ,
                                                int lower_bckgrd_plus ,
                                                int higher_bckgrd_plus ,
                                                int lower_bckgrd_minus ,
                                                int higher_bckgrd_minus ,
                                                int offset = 0) ;

    vector<double>  get_error_asymmetry_vector(int histo_num_plus ,
                                                int histo_num_minus ,
                                                double alpha_param ,
                                                int binning ,
                                                int lower_bckgrd_plus ,
                                                int higher_bckgrd_plus ,
                                                int lower_bckgrd_minus ,
                                                int higher_bckgrd_minus ,
                                                int offset = 0) ;

    double         *get_asymmetry_goodBins_array(int histo_num_plus ,
                                                  int histo_num_minus ,
                                                  double alpha_param ,
                                                  int binning ,
                                                  int lower_bckgrd_plus ,
                                                  int higher_bckgrd_plus ,
                                                  int lower_bckgrd_minus ,
                                                  int higher_bckgrd_minus) ;

    vector<double> get_asymmetry_goodBins_vector(int histo_num_plus ,
                                                  int histo_num_minus ,
                                                  double alpha_param ,
                                                  int binning ,
                                                  int lower_bckgrd_plus ,
                                                  int higher_bckgrd_plus ,
                                                  int lower_bckgrd_minus ,
                                                  int higher_bckgrd_minus) ;

    double        *get_error_asymmetry_goodBins_array(int histo_num_plus ,
                                                       int histo_num_minus ,
                                                       double alpha_param ,
                                                       int binning ,
                                                       int lower_bckgrd_plus ,
                                                       int higher_bckgrd_plus ,
                                                       int lower_bckgrd_minus ,
                                                       int higher_bckgrd_minus) ;

    vector<double> get_error_asymmetry_goodBins_vector(int histo_num_plus ,
                                                        int histo_num_minus ,
                                                        double alpha_param ,
                                                        int binning ,
                                                        int lower_bckgrd_plus ,
                                                        int higher_bckgrd_plus ,
                                                        int lower_bckgrd_minus ,
                                                        int higher_bckgrd_minus) ;


    double          get_binWidth_ps();
    double          get_binWidth_ns();
    double          get_binWidth_us();

    int             get_histoLength_bin();

    int             get_numberHisto_int();

    string          get_nameHisto(int i) ;
    vector<string>  get_histoNames_vector();

    long            get_eventsHisto_long(int i);
    vector<long>    get_eventsHisto_vector();

    long            get_totalEvents_long();

    int             get_numberScaler_int();
    vector<long>    get_scalers_vector() ;
    vector<string>  get_scalersNames_vector() ;

    int             get_default_binning() ;
    int             get_t0_int(int i) ;
    vector<int>     get_t0_vector() ;
    double          get_t0_double(int i) ;

    int             get_max_t0_int () ;
    int             get_max_2_t0_int (int k, int j) ;
    int             get_min_t0_int () ;
    int             get_min_2_t0_int (int k, int j) ;

    int             get_firstGood_int(int i) ;
    vector<int>     get_firstGood_vector() ;
    int             put_firstGood_int(int i, int j) ;

    int             get_lastGood_int(int i) ;
    vector<int>     get_lastGood_vector() ;
    int             put_lastGood_int(int i, int j) ;

    int             get_max_lastGood_int () ;
    int             get_max_2_lastGood_int (int k, int j) ;
    int             get_min_lastGood_int () ;
    int             get_min_2_lastGood_int (int k, int j) ;

    int             get_runNumber_int() ;
    int             put_runNumber_int(int i) ;

    string          get_sample() ;
    string          get_field() ;
    string          get_orient() ;
    string          get_temp() ;
    string          get_comment() ;

    vector<string>  get_timeStart_vector() ;
    vector<string>  get_timeStop_vector() ;

    int             get_numberTemperature_int() ;
    vector<double>  get_temperatures_vector() ;
    vector<double>  get_devTemperatures_vector() ;

  private:

    int tmax(int x, int y) ;
    int tmin(int x, int y) ;

} ;
#endif
/************************************************************************************
 * EOF MuSR_td_PSI_bin.h                                                         *
 ************************************************************************************/
