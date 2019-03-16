#include "mud.h"

int 
readingMuSRFiles(int argc, char* argv[])
{
	UINT32 pType[1];
	printf("Opening %s to read ...\n",argv[1]);

	int fh = MUD_openRead(argv[1], pType);

	FILE * fp;
	fp = fopen(argv[2],"w");
	

	fprintf(fp, "#ExptNumber, RunNumber, ElapsedSecs, TimeBegin, TimeEnd, Title, Lab, Area, Method, Apparatus, Insert, Sample, Orient, Das, Experimenters, Temperature, Field, NumHists\n");
	UINT32 pExptNumber[1];
	MUD_getExptNumber(fh, pExptNumber);
	fprintf(fp, "%d, ",pExptNumber[0]);

	UINT32 pRunNumber[1];
	MUD_getRunNumber(fh, pRunNumber);
	fprintf(fp, "%d, ",pRunNumber[0]);

	UINT32 pElapsedSec[1];
	MUD_getElapsedSec(fh, pElapsedSec);
	fprintf(fp, "%d, ",pElapsedSec[0]);

	UINT32 TimeBegin[1];
	MUD_getTimeBegin(fh, TimeBegin);
	fprintf(fp, "%d, ",TimeBegin[0]);

	UINT32 TimeEnd[1];
	MUD_getTimeEnd(fh, TimeEnd);
	fprintf(fp, "%d, ",TimeEnd[0]);

	char title[48];
	MUD_getTitle(fh, title, 48);
	fprintf(fp, "%s, ",title);

	char lab[16];
	MUD_getLab(fh, lab, 16);
	fprintf(fp, "%s, ",lab);

	char area[16];
	MUD_getArea(fh, area, 16);
	fprintf(fp, "%s, ",area);

	char method[16];
	MUD_getMethod(fh, method, 16);
	fprintf(fp, "%s, ",method);

	char apparatus[16];
	MUD_getApparatus(fh, apparatus, 16);
	fprintf(fp, "%s, ",apparatus);

	char insert[16];
	MUD_getInsert(fh, insert, 16);
	fprintf(fp, "%s, ",insert);

	char sample[16];
	MUD_getSample(fh, sample, 16);
	fprintf(fp, "%s, ",sample);

	char orient[16];
	MUD_getOrient(fh, orient, 16);
	fprintf(fp, "%s, ",orient);

	char das[16];
	MUD_getDas(fh, das, 16);
	fprintf(fp, "%s, ",das);

	char experimenter[32];
	MUD_getExperimenter(fh, experimenter, 32);
	fprintf(fp, "%s, ",experimenter);

	char temperature[16];
	MUD_getTemperature(fh, temperature, 16);
	fprintf(fp, "%s, ",temperature);

	char field[16];
	MUD_getField(fh, field, 16);
	fprintf(fp, "%s, ",field);

	UINT32 pNum[1];
	MUD_getHists(fh, pType, pNum);
	fprintf(fp, "%d\n",pNum[0]);


	UINT32 histogramNumber = 1;
	UINT32 pNumBins[1];
	MUD_getHistNumBins(fh, histogramNumber, pNumBins);
	UINT32 pData_one[pNumBins[0]];
	void *p = &pData_one;
	MUD_getHistData(fh,histogramNumber,pData_one);
	REAL64 pSecondsPerBin[1];
	MUD_getHistSecondsPerBin(fh, histogramNumber, pSecondsPerBin);
	fprintf(fp, "%u, %.16lf\n", pNumBins[0],pSecondsPerBin[0]);


	histogramNumber += 1;
	MUD_getHistNumBins(fh, histogramNumber, pNumBins);
	UINT32 pData_two[pNumBins[0]];
	p = &pData_two;
	MUD_getHistData(fh,histogramNumber,pData_two);
	MUD_getHistSecondsPerBin(fh, histogramNumber, pSecondsPerBin);
	fprintf(fp, "%u, %.16lf\n", pNumBins[0],pSecondsPerBin[0]);


	histogramNumber += 1;
	MUD_getHistNumBins(fh, histogramNumber, pNumBins);
	UINT32 pData_three[pNumBins[0]];
	p = &pData_three;
	MUD_getHistData(fh,histogramNumber,pData_three);
	MUD_getHistSecondsPerBin(fh, histogramNumber, pSecondsPerBin);
	fprintf(fp, "%u, %.16lf\n", pNumBins[0],pSecondsPerBin[0]);


	histogramNumber += 1;
	MUD_getHistNumBins(fh, histogramNumber, pNumBins);
	UINT32 pData_four[pNumBins[0]];
	p = &pData_four;
	MUD_getHistData(fh,histogramNumber,pData_four);
	MUD_getHistSecondsPerBin(fh, histogramNumber, pSecondsPerBin);
	fprintf(fp, "%u, %.16lf\n", pNumBins[0],pSecondsPerBin[0]);


	for(UINT32 i = 0; i < pNumBins[0]-1; i++)
	{
		fprintf(fp,"%u, ",pData_one[i]);
		fprintf(fp,"%u, ",pData_two[i]);
		fprintf(fp,"%u, ",pData_three[i]);
		fprintf(fp,"%u",pData_four[i]);
		fprintf(fp,"\n");
	}


	memset(pData_one,0,sizeof pData_one);
	memset(pData_two,0,sizeof pData_two);
	memset(pData_one,0,sizeof pData_three);
	memset(pData_two,0,sizeof pData_four);


	fclose(fp);
	MUD_closeRead(fh);

	

	return 0;
}