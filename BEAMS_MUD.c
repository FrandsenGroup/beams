#include "mud.h"
#include "BEAMS_MUD.h"
#include <string.h>
#include <stdbool.h>

int 
readingMuSRFiles(int argc, char* argv[])
{
	bool read_header = true;
	bool read_histogram = true;
	
	for(int i = 0; i < argc; i++)
	{
		if(strcmp(argv[i],"-hist"))
		{
			read_header = false;
		}
		else if(strcmp(argv[i],"-head"))
		{
			read_histogram = false;
		}
	}	

	
	UINT32 pType[1];
	printf("Opening %s to read ...\n",argv[1]);

	int fh = MUD_openRead(argv[1], pType);
	FILE * fp;

	printf("Opening %s to write ... \n\n",argv[2]);
	fp = fopen(argv[2],"w");
	

	if(read_header)
	{
		printf("Retrieving header data ... \n");

		fprintf(fp, "BEAMS\nExptNumber,RunNumber,ElapsedSecs,TimeBegin,TimeEnd,Title,Lab,Area,Method,Apparatus,Insert,Sample,Orient,Das,Experimenters,Temperature,Field,NumHists,numBins,binsize\n");
		UINT32 pExptNumber[1];
		MUD_getExptNumber(fh, pExptNumber);
		fprintf(fp, "%d,",pExptNumber[0]);
	
		UINT32 pRunNumber[1];
		MUD_getRunNumber(fh, pRunNumber);
		fprintf(fp, "%d,",pRunNumber[0]);

		UINT32 pElapsedSec[1];
		MUD_getElapsedSec(fh, pElapsedSec);
		fprintf(fp, "%d,",pElapsedSec[0]);

		UINT32 TimeBegin[1];
		MUD_getTimeBegin(fh, TimeBegin);
		fprintf(fp, "%d,",TimeBegin[0]);

		UINT32 TimeEnd[1];
		MUD_getTimeEnd(fh, TimeEnd);
		fprintf(fp, "%d,",TimeEnd[0]);

		char title[48];
		MUD_getTitle(fh, title, 48);
		fprintf(fp, "%s,",title);

		char lab[16];
		MUD_getLab(fh, lab, 16);
		fprintf(fp, "%s,",lab);

		char area[16];
		MUD_getArea(fh, area, 16);
		fprintf(fp, "%s,",area);
 
		//FIXME Problem reading in the µ symbol
		char method[4];
		MUD_getMethod(fh, method, 4);
		fprintf(fp, "%s,",method);

		char apparatus[16];
		MUD_getApparatus(fh, apparatus, 16);
		fprintf(fp, "%s,",apparatus);

		char insert[16];
		MUD_getInsert(fh, insert, 16);
		fprintf(fp, "%s,",insert);

		char sample[16];
		MUD_getSample(fh, sample, 16);
		fprintf(fp, "%s,",sample);

		char orient[16];
		MUD_getOrient(fh, orient, 16);
		fprintf(fp, "%s,",orient);

		char das[16];
		MUD_getDas(fh, das, 16);
		fprintf(fp, "%s,",das);

		char experimenter[32];
		MUD_getExperimenter(fh, experimenter, 32);
		fprintf(fp, "%s,",experimenter);

		char temperature[16];
		MUD_getTemperature(fh, temperature, 16);
		fprintf(fp, "%s,",temperature);

		char field[16];
		MUD_getField(fh, field, 16);
		fprintf(fp, "%s,",field);
	}


	if(read_histogram)
	{
		UINT32 num_hists[1];
		MUD_getHists(fh, pType, num_hists);
		fprintf(fp, "%d,",num_hists[0]);
	
		printf("Retrieving histogram data ...\n");

		UINT32 max_bins[1];
		UINT32 min_bins[1];
		MUD_getHistNumBins(fh, 1, max_bins);
		MUD_getHistNumBins(fh, 1, min_bins);

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 num_bins[1];
			MUD_getHistNumBins(fh, i+1, num_bins);

			if(num_bins[0] > max_bins[0])
			{
				max_bins[0] = num_bins[0];
			}
			else if(num_bins[0] < min_bins[0])
			{
				min_bins[0] = num_bins[0];
			}
		}

		UINT32 all_histograms[num_hists[0]][max_bins[0]];

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			char hist_title[32];
			UINT32 num_bins[1];
			
			MUD_getHistTitle(fh, i+1, hist_title, 32);
			MUD_getHistNumBins(fh, i+1, num_bins);
			
			void *data_pointer = &all_histograms[i];
			
			MUD_getHistData(fh, i+1, data_pointer);

			fprintf(fp, "%s", hist_title);
			
			if(i < num_hists[0]-1)
			{
				fprintf(fp,", ");
			}
			else
			{
				fprintf(fp,"\n");
			}

			printf("Retrieved data from histogram %d (%s), with %d bins.\n",i+1,hist_title,num_bins[0]);		
		}
			
		printf("Writing histogram data to file ...\n");

		for(UINT32 i = 0; i < min_bins[0]; i++)
		{
			for(UINT32 j = 0; j < num_hists[0]-1; j++)
			{
				fprintf(fp, "%u,",all_histograms[j][i]);
			}
			fprintf(fp, "%u\n",all_histograms[num_hists[0]-1][i]);
		}

		memset(all_histograms, 0, sizeof all_histograms);
	}	

	/*
	char app_lampf[16] = "LAMPF";
	if(strcmp(apparatus,app_lampf) == 0){
		printf("%s : %s\nLAMPF Method\n",apparatus,app_lampf);
	}
	
	REAL64 pSecondsPerBin[1];
	MUD_getHistSecondsPerBin(fh, histogramNumber, pSecondsPerBin);
	fprintf(fp, "%u,%.16lf\n", pNumBins[0],pSecondsPerBin[0]*1000000000);
	*/
	

	printf("Done. \n\nClosing %s ...\n",argv[2]);

	fclose(fp);

	printf("Closing %s ... \n\n", argv[1]);
	MUD_closeRead(fh);

	printf("Exited with 0 errors.\n");

	return 0;
}
