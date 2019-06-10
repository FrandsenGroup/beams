#include "mud.h"
#include "BEAMS_MUD.h"
#include <string.h>
#include <stdbool.h>

int 
readingMuSRFiles(int argc, char* argv[])
{
	int header_rows = 8;

	bool read_header = true;
	bool read_histogram = true;
	bool verbose = false;

	bool read_expt_number = false;
	bool read_run_number = false;
	bool read_elapsed_secs = false;
	bool read_time_begin = false;
	bool read_time_end = false;
	bool read_title = false;
	bool read_lab = false;
	bool read_area = false;
	bool read_method = false;
	bool read_apparatus = false;
	bool read_insert = false;
	bool read_sample = false;
	bool read_orient = false;
	bool read_das = false;
	bool read_experimenters = false;
	bool read_temperature = false;
	bool read_field = false;
	bool read_num_hists = false;
	bool read_num_bins = false;
	bool read_bin_size = true;

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
		else if(strcmp(argv[i], "-en") == 0)
		{
			read_expt_number = true;
		}
		else if(strcmp(argv[i], "-rn") == 0)
		{
			read_run_number = true;
		}
		else if(strcmp(argv[i], "-es") == 0)
		{
			read_elapsed_secs = true;
		}
		else if(strcmp(argv[i], "-tb") == 0)
		{
			read_time_begin = true;
		}
		else if(strcmp(argv[i], "-te") == 0)
		{
			read_time_end = true;
		}
		else if(strcmp(argv[i], "-ti") == 0)
		{
			read_title = true;
		}
		else if(strcmp(argv[i], "-lb") == 0)
		{
			read_lab = true;
		}
		else if(strcmp(argv[i], "-ar") == 0)
		{
			read_area = true;
		}
		else if(strcmp(argv[i], "-me") == 0)
		{
			read_method = true;
		}
		else if(strcmp(argv[i], "-ap") == 0)
		{
			read_apparatus = true;
		}
		else if(strcmp(argv[i], "-in") == 0)
		{
			read_insert = true;
		}
		else if(strcmp(argv[i], "-sa") == 0)
		{
			read_sample = true;
		}
		else if(strcmp(argv[i], "-or") == 0)
		{
			read_orient = true;
		}
		else if(strcmp(argv[i], "-da") == 0)
		{
			read_das = true;
		}
		else if(strcmp(argv[i], "-ex") == 0)
		{
			read_experimenters = true;
		}
		else if(strcmp(argv[i], "-tp") == 0)
		{
			read_temperature = true;
		}
		else if(strcmp(argv[i], "-fd") == 0)
		{
			read_field = true;
		}
		else if(strcmp(argv[i], "-nh") == 0)
		{
			read_num_hists = true;
		}
		else if(strcmp(argv[i], "-nb") == 0)
		{
			read_num_bins = true;
		}
		else if(strcmp(argv[i], "-all") == 0)
		{
		bool read_expt_number = true;
		read_run_number = true;
		read_elapsed_secs = true;
		read_time_begin = true;
		read_time_end = true;
		read_title = true;
		read_lab = true;
		read_area = true;
		read_method = true;
		read_apparatus = true;
		read_insert = true;
		read_sample = true;
		read_orient = true;
		read_das = true;
		read_experimenters = true;
		read_temperature = true;
		read_field = true;
		read_num_hists = true;
		read_num_bins = true;
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

		fprintf(fp, "BEAMS\nHeaderRows:%d", header_rows);
		if (verbose)
		    printf("\tHeaderRows : %d\n", header_rows);

	    if (read_bin_size)
	    {
	        REAL64 pData[1];
	        MUD_getHistSecondsPerBin(fh, 1, pData);
            	fprintf(fp, ",BinSize:%.16lf", pData[0]*1000000000);
            	if (verbose)
                	printf("\tBinSize : %.16lf\n", pData[0]*1000000000);
        	}
	    if (read_expt_number)
	    {
	        UINT32 pData[1];
	        MUD_getExptNumber(fh, pData);
	        fprintf(fp, ",ExptNumber:%d", pData[0]);
	        if(verbose)
	            printf("\tExptNumber : %d\n", pData[0]);
        }
		if (read_run_number)
		{
		    UINT32 pData[1];
		    MUD_getRunNumber(fh, pData);
		    fprintf(fp, ",RunNumber:%d", pData[0]);
		    if(verbose)
	            printf("\tRunNumber : %d\n", pData[0]);
        }
	    if (read_title)
	    {
	        char pData[48];
	        MUD_getTitle(fh, pData, 48);
	        fprintf(fp, ",Title:%s", pData);
	        if(verbose)
	            printf("\tTitle : %s\n", pData);
	    }
	    if (read_lab)
	    {
	        char pData[16];
	        MUD_getLab(fh, pData, 16);
	        fprintf(fp, ",Lab:%s", pData);
	        if(verbose)
	            printf("\tLab : %s\n", pData);
	    }
	    if (read_area)
	    {
	        char pData[16];
	        MUD_getArea(fh, pData, 16);
	        fprintf(fp, ",Area:%s", pData);
	        if(verbose)
	            printf("\tArea : %s\n", pData);
	    }
	    if (read_temperature)
	    {
	        char pData[16];
	        MUD_getTemperature(fh, pData, 16);
	        fprintf(fp, ",Temperature:%s", pData);
	        if(verbose)
	            printf("\tTemperature : %s\n", pData);
	    }
	    if (read_field)
	    {
	        char pData[16];
	        MUD_getField(fh, pData, 16);
	        fprintf(fp, ",Field:%s", pData);
	        if(verbose)
	            printf("\tField : %s\n", pData);
	    }
	    if (read_time_begin)
	    {
	        UINT32 pData[1];
	        MUD_getTimeBegin(fh, pData);
	        fprintf(fp, ",BeginTime:%d", pData[0]);
	        if(verbose)
	            printf("\tBeginTime : %d\n", pData[0]);
	    }
	    if (read_time_end)
	    {
	        UINT32 pData[1];
	        MUD_getTimeEnd(fh, pData);
	        fprintf(fp, ",EndTime:%d", pData[0]);
	        if(verbose)
	            printf("\tEndTime : %d\n", pData[0]);
	    }
	    if (read_elapsed_secs)
	    {
	        UINT32 pData[1];
	        MUD_getElapsedSec(fh, pData);
	        fprintf(fp, ",ElapsedSecs:%d", pData[0]);
	        if(verbose)
	            printf("\tElapsedSecs : %d\n", pData[0]);
	    }
	    if (read_method)
	    {
	        char pData[4];
	        MUD_getMethod(fh, pData, 4);
	        fprintf(fp, ",Method:%s", pData);
	        if(verbose)
	            printf("\tMethod : %s\n", pData);
	    }
	    if (read_apparatus)
	    {
            char pData[16];
            MUD_getApparatus(fh, pData, 16);
            fprintf(fp, ",Apparatus:%s", pData);
            if(verbose)
	            printf("\tApparatus : %s\n", pData);
	    }
	    if (read_insert)
	    {
            char pData[16];
            MUD_getInsert(fh, pData, 16);
            fprintf(fp, ",Insert:%s", pData);
            if(verbose)
	            printf("\tInsert : %s\n", pData);
	    }
	    if (read_sample)
	    {
            char pData[16];
            MUD_getSample(fh, pData, 16);
            fprintf(fp, ",Sample:%s", pData);
            if(verbose)
	            printf("\tSample : %s\n", pData);
	    }
	    if (read_orient)
	    {
            char pData[16];
            MUD_getOrient(fh, pData, 16);
            fprintf(fp, ",Orientation:%s", pData);
            if(verbose)
	            printf("\tOrientation : %s\n", pData);
	    }
	    if (read_das)
	    {
            char pData[16];
            MUD_getDas(fh, pData, 16);
            fprintf(fp, ",Das:%s", pData);
            if(verbose)
	            printf("\tDas : %s\n", pData);
	    }
	    if (read_num_hists)
	    {
            UINT32 pData[1];
            MUD_getHists(fh, pType, pData);
            fprintf(fp, ",NumHists:%d", pData[0]);
            if(verbose)
	            printf("\tNumHists : %d\n", pData[0]);
	    }
	    if (read_num_bins)
	    {
            UINT32 pData[1];
            MUD_getHistNumBins(fh, 1, pData);
            fprintf(fp, ",NumBins:%d", pData[0]);
            if(verbose)
	            printf("\tNumBins : %d\n", pData[0]);
	    }
	    if (read_experimenters)
	    {
            char pData[32];
            MUD_getExperimenter(fh, pData, 32);
            fprintf(fp, ",Experimenters:%s", pData);
            if(verbose)
	            printf("\tExperimenters : %s\n", pData);
	    }
		printf("\n");
	    fprintf(fp, "\n");
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
				fprintf(fp,",");
			}
			else
			{
				fprintf(fp,"\n");
			}

			if (verbose)
				printf("\tRetrieved data from histogram %d (%s), with %d bins.\n",i+1,hist_title,num_bins[0]);		
		}

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 Bkgd1[1];
			MUD_getHistBkgd1(fh, i+1, Bkgd1);
			fprintf(fp, "%d", Bkgd1[0]);
			if(i < num_hists[0]-1)
			{
				fprintf(fp, ",");
			}
			else
			{
				fprintf(fp, "\n");
			}
		}

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 Bkgd2[1];
			MUD_getHistBkgd2(fh, i+1, Bkgd2);
			fprintf(fp, "%d", Bkgd2[0]);
			if(i < num_hists[0]-1)
			{
				fprintf(fp, ",");
			}
			else
			{
				fprintf(fp, "\n");
			}
		}

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 GoodBin1[1];
			MUD_getHistGoodBin1(fh, i+1, GoodBin1);
			fprintf(fp, "%d", GoodBin1[0]);
			if(i < num_hists[0]-1)
			{
				fprintf(fp, ",");
			}
			else
			{
				fprintf(fp, "\n");
			}
		}

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 GoodBin2[1];
			MUD_getHistGoodBin2(fh, i+1, GoodBin2);
			fprintf(fp, "%d", GoodBin2[0]);
			if(i < num_hists[0]-1)
			{
				fprintf(fp, ",");
			}
			else
			{
				fprintf(fp, "\n");
			}
		}

		for(UINT32 i = 0; i < num_hists[0]; i++)
		{
			UINT32 T0[1];
			MUD_getHistT0_Bin(fh, i+1, T0);
			fprintf(fp, "%d", T0[0]);
			if(i < num_hists[0]-1)
			{
				fprintf(fp, ",");
			}
			else
			{
				fprintf(fp, "\n");
			}
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
