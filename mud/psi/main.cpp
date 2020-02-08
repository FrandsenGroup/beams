#include <iostream>
#include <fstream>
#include <vector>
#include <string>

#include "MuSR_td_PSI_bin.h"

string remove_whitespace(string newString) {
    string retString;
    for(unsigned int i = 0; i < newString.size(); i++) {
        char currentChar = newString.at(i);
        if((isalnum(currentChar) || ispunct(currentChar)) || (isspace(currentChar) && i < newString.size()-1 && !isspace(newString.at(i+1)))) {
            retString.push_back(currentChar);
        }
    }
    return retString;
}

int main( int argc, char ** argv )

  {
    MuSR_td_PSI_bin bin_reader;
    ofstream outFile;

    bin_reader.read(argv[1]);

    int numHists = bin_reader.get_numberHisto_int();
    int numBins = bin_reader.get_histoLength_bin();
    vector<vector<double>> hists;
    int firstBackground;
    int lastBackground;

    for(unsigned int i = 0; i < numHists; i++) {
        hists.push_back(bin_reader.get_histo_vector(i, 1));
    }

    double binWidth = bin_reader.get_binWidth_ns();
    vector<int> t0Bins = bin_reader.get_t0_vector();
    vector<int> firstGoodBins = bin_reader.get_firstGood_vector();
    vector<int> lastGoodBins = bin_reader.get_lastGood_vector();
    int runNumber = bin_reader.get_runNumber_int();
    string sampleName = bin_reader.get_sample();
    string temperature = bin_reader.get_temp();
    string orientation = bin_reader.get_orient();
    string field = bin_reader.get_field();
    string comment = bin_reader.get_comment();
    vector<string> histNames = bin_reader.get_histoNames_vector();
    vector<string> scalers = bin_reader.get_scalersNames_vector();

    for(unsigned int i = 0; i < firstGoodBins.at(0); i++){
        if(hists.at(0).at(i) != 0 && hists.at(0).at(i+1) != 0) {
            firstBackground = i;
            break;
        }
    }
    lastBackground = firstGoodBins.at(0) - 5;

    outFile.open(argv[2]);

    outFile << "BEAMS" << endl;

    outFile << "BinSize:" << binWidth;
    outFile << ",Temperature:" << remove_whitespace(temperature);
    outFile << ",Field:" << remove_whitespace(field);
    outFile << ",Sample:" << remove_whitespace(sampleName);
    outFile << ",Orientation:" << remove_whitespace(orientation);
    outFile << ",NumBins:" << numBins;
    outFile << ",NumHists:" << numHists;
    outFile << ",RunNumber:" << runNumber;
    outFile << ",Title:" << remove_whitespace(comment) << endl;

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << remove_whitespace(histNames.at(i));
    }
    outFile << "\n";

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << firstBackground;
    }
    outFile << "\n";

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << lastBackground;
    }
    outFile << "\n";

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << firstGoodBins.at(i);
    }
    outFile << "\n";

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << lastGoodBins.at(i);
    }
    outFile << "\n";

    for(unsigned int i = 0; i < numHists; i++) {
        if(i > 0 && i < numHists) {
            outFile << ",";
        }
        outFile << t0Bins.at(i);
    }
    outFile << "\n";

    for(unsigned int j = 0; j < numBins; j++) {
        for(unsigned int i = 0; i < numHists; i++) {
            if(i > 0 && i < numHists) {
                outFile << ",";
            }
            outFile << hists.at(i).at(j);
        }
        outFile << "\n";
    }

    return 0;
  }

