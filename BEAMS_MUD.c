#include "mud.h"
#include "BEAMS_MUD.h"
#include <string.h>
#include <stdbool.h>

int 
readingMuSRFiles(int argc, char* argv[])
{
	bool read_header = true;
	bool read_histogram = true;
	bool verbose = false;

	for(int i = 0; i < argc; i++)
	{
		if(strcmp(argv[i],"-hist") == 0)
		{
			read_histogram = false;
		}
		else if(strcmp(argv[i],"-head") == 0)
		{
			read_header = false;
		}
		else if(strcmp(argv[i],"-v") == 0)
		{
			verbose = true;
		}
	}	
	
	UINT32 pType[1];

	if (verbose)
		printf("Opening %s to read ...\n",argv[1]);

	int fh = MUD_openRead(argv[1], pType);
	FILE * fp;

	if (verbose)
		printf("Opening %s to write ... \n\n",argv[2]);
	
	fp = fopen(argv[2],"w");
	
	
	if(read_header == true)
	{
		if (verbose)
			printf("Retrieving header data ... \n\n");

		fprintf(fp, "BEAMS\nExptNumber,RunNumber,ElapsedSecs,TimeBegin,TimeEnd,Title,Lab,Area,Method,Apparatus,Insert,Sample,Orient,Das,Experimenters,Temperature,Field,NumHists,numBins,binsize\n");
		UINT32 pExptNumber[1];
		MUD_getExptNumber(fh, pExptNumber);
		fprintf(fp, "%d,",pExptNumber[0]);
	
		if(verbose)
			printf("\tExperiment Number : %d\n", pExptNumber[0]);

		UINT32 pRunNumber[1];
		MUD_getRunNumber(fh, pRunNumber);
		fprintf(fp, "%d,",pRunNumber[0]);

		if(verbose)
			printf("\tRun Number : %d\n", pRunNumber);

		UINT32 pElapsedSec[1];
		MUD_getElapsedSec(fh, pElapsedSec);
		fprintf(fp, "%d,",pElapsedSec[0]);

		if(verbose)
			printf("\tElapsed Seconds : %d\n", pElapsedSec[0]);

		UINT32 TimeBegin[1];
		MUD_getTimeBegin(fh, TimeBegin);
		fprintf(fp, "%d,",TimeBegin[0]);

		if(verbose)
			printf("\tBeginning Time : %d\n", TimeBegin[0]);

		UINT32 TimeEnd[1];
		MUD_getTimeEnd(fh, TimeEnd);
		fprintf(fp, "%d,",TimeEnd[0]);

		if(verbose)
			printf("\tEnding Time: %d\n", TimeEnd[0]);

		char title[48];
		MUD_getTitle(fh, title, 48);
		fprintf(fp, "%s,",title);

		if(verbose)
			printf("\tRun Title : %s\n", title);

		char lab[16];
		MUD_getLab(fh, lab, 16);
		fprintf(fp, "%s,",lab);

		if(verbose)
			printf("\tLab : %s\n", lab);

		char area[16];
		MUD_getArea(fh, area, 16);
		fprintf(fp, "%s,",area);

		if(verbose)
			printf("\tArea : %s\n", area);
 
		//FIXME Problem reading in the µ symbol
		char method[4];
		MUD_getMethod(fh, method, 4);
		fprintf(fp, "%s,",method);

		if(verbose)
			printf("\tMethod : %s\n", method);

		char apparatus[16];
		MUD_getApparatus(fh, apparatus, 16);
		fprintf(fp, "%s,",apparatus);

		if(verbose)
			printf("\tApparatus : %s\n", apparatus);

		char insert[16];
		MUD_getInsert(fh, insert, 16);
		fprintf(fp, "%s,",insert);

		if(verbose)
			printf("\tInsert : %s\n", insert);

		char sample[16];
		MUD_getSample(fh, sample, 16);
		fprintf(fp, "%s,",sample);

		if(verbose)
			printf("\tSample : %s\n", sample);

		char orient[16];
		MUD_getOrient(fh, orient, 16);
		fprintf(fp, "%s,",orient);

		if(verbose)
			printf("\tOrientation : %s\n", orient);

		char das[16];
		MUD_getDas(fh, das, 16);
		fprintf(fp, "%s,",das);

		if(verbose)
			printf("\tDas : %s\n", das);

		char experimenter[32];
		MUD_getExperimenter(fh, experimenter, 32);
		fprintf(fp, "%s,",experimenter);

		if(verbose)
			printf("\tExperimenter(s) : %s\n", experimenter); 

		char temperature[16];
		MUD_getTemperature(fh, temperature, 16);
		fprintf(fp, "%s,",temperature);

		if(verbose)
			printf("\tTemperature : %s\n", temperature);

		char field[16];
		MUD_getField(fh, field, 16);
		fprintf(fp, "%s,",field);

		if(verbose)
			printf("\tField : %s\n", field);

		UINT32 histsNum[1];
		MUD_getHists(fh, pType, histsNum);
		fprintf(fp,"%d,",histsNum);

		if(verbose)
			printf("\t# of Histograms : %d\n", histsNum[0]);

		UINT32 binsNum[1];
		MUD_getHistNumBins(fh, 1, binsNum);
		fprintf(fp,"%d",binsNum[0]);

		if(verbose)
			printf("\t# of Bins : %d\n", binsNum[0]);

		REAL64 secsPerBin[1];
		MUD_getHistSecondsPerBin(fh, 1, secsPerBin);
		fprintf(fp,"%.16lf\n",secsPerBin[0]*1000000000);

		if(verbose)
			printf("\tBin Size : %.16lf\n\n", secsPerBin[0]); 
		
	}


	if(read_histogram)
	{
		UINT32 num_hists[1];
		MUD_getHists(fh, pType, num_hists);
	
		if (verbose)
			printf("Retrieving histogram data ...\n\n");

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

			if (verbose)
				printf("\tRetrieved data from histogram %d (%s), with %d bins.\n",i+1,hist_title,num_bins[0]);		
		}
		
		if (verbose)
			printf("\nWriting histogram data to file ...\n");

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

	if (verbose)
		printf("Done. \n\nClosing %s ...\n",argv[2]);

	fclose(fp);

	if (verbose)
		printf("Closing %s ... \n\n", argv[1]);
	
	MUD_closeRead(fh);

	if (verbose)
		printf("Exited with 0 errors.\n");

	return 0;
}
