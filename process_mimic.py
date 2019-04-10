# This script processes MIMIC-III dataset and builds longitudinal diagnosis records for patients with at least two visits.
# The output data are cPickled, and suitable for training Doctor AI or RETAIN
# Written by Edward Choi (mp2893@gatech.edu)
# Usage: Put this script to the foler where MIMIC-III CSV files are located. Then execute the below command.
# python process_mimic.py ADMISSIONS.csv DIAGNOSES_ICD.csv <output file> 

# Output files
# <output file>.pids: List of unique Patient IDs. Used for intermediate processing
# <output file>.dates: List of List of Python datetime objects. The outer List is for each patient. The inner List is for each visit made by each patient
# <output file>.seqs: List of List of List of integer diagnosis codes. The outer List is for each patient. The middle List contains visits made by each patient. The inner List contains the integer diagnosis codes that occurred in each visit
# <output file>.types: Python dictionary that maps string diagnosis codes to integer diagnosis codes.

import sys
import cPickle as pickle
from datetime import datetime
import pandas as pd

def convert_to_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4] + '.' + dxStr[4:]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3] + '.' + dxStr[3:]
		else: return dxStr
	
def convert_to_3digit_icd9(dxStr):
	if dxStr.startswith('E'):
		if len(dxStr) > 4: return dxStr[:4]
		else: return dxStr
	else:
		if len(dxStr) > 3: return dxStr[:3]
		else: return dxStr

def convert_to_label(dxStr):
    return 'D_' + convert_to_icd9(dxStr[1:-1])

if __name__ == '__main__':
	admissionFile = sys.argv[1]
	diagnosisFile = sys.argv[2]
	outFile = sys.argv[3]

	# label file location
	PATH_LABELMAP = "labelMap.csv"
	df_map = pd.read_csv("labelMap.csv", usecols=["code", "cat"])
	df_map["code"] = df_map["code"].apply(convert_to_label)
	CCSMapping = dict(zip(df_map.code, df_map.cat))

	print 'Building pid-admission mapping, admission-date mapping'
	pidAdmMap = {}
	admDateMap = {}
	infd = open(admissionFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		pid = int(tokens[1])
		admId = int(tokens[2])
		admTime = datetime.strptime(tokens[3], '%Y-%m-%d %H:%M:%S')
		admDateMap[admId] = admTime
		if pid in pidAdmMap: pidAdmMap[pid].append(admId)
		else: pidAdmMap[pid] = [admId]
	infd.close()

	print 'Building admission-dxList mapping'
	admDxMap = {}
	infd = open(diagnosisFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		admId = int(tokens[2])
		dxStr = 'D_' + convert_to_icd9(tokens[4][1:-1]) ############## Uncomment this line and comment the line below, if you want to use the entire ICD9 digits.
		#dxStr = 'D_' + convert_to_3digit_icd9(tokens[4][1:-1])
		if admId in admDxMap: admDxMap[admId].append(dxStr)
		else: admDxMap[admId] = [dxStr]
	infd.close()

	print 'Building pid-sortedVisits mapping'
	pidSeqMap = {}
	for pid, admIdList in pidAdmMap.iteritems():
		if len(admIdList) < 2: continue
		sortedList = sorted([(admDateMap[admId], admDxMap[admId]) for admId in admIdList])
		pidSeqMap[pid] = sortedList
	
	print 'Building pids, dates, strSeqs'
	pidsTrain = []
	datesTrain = []
	seqsTrain = []
	pidsValid = []
	datesValid = []
	seqsValid = []
	pidsTest = []
	datesTest = []
	seqsTest = []
	i = 0

	def appendToList(pid, visits, pids, dates, seqs):
		pids.append(pid)
		seq = []
		date = []
		for visit in visits:
			date.append(visit[0])
			seq.append(visit[1])
		dates.append(date)
		seqs.append(seq)

	# split the data into train, test, valid sets, with ratio of 8:1:1
	for pid, visits in pidSeqMap.iteritems():
		if i < 8:
			appendToList(pid, visits, pidsTrain, datesTrain, seqsTrain)
		elif i < 9:
			appendToList(pid, visits, pidsTest, datesTest, seqsTest)
		else:
			appendToList(pid, visits, pidsValid, datesValid, seqsValid)	
		i = (i+1)%10
	
	print 'Converting strSeqs to intSeqs, and making types'
	types = {}

	def genNewSeqs(seqs, types, mapping):
		newSeqs = []
		newLabels = []
		# print seqs[0][0]
		
		for patient in seqs:
			newPatient = []
			newPatientLabel = []
			for visit in patient:
				newVisit = []
				newVisitLabel = []
				for code in visit:
					if code not in types:
						types[code] = len(types)
					newVisit.append(types[code])
					if code not in mapping:
						newVisitLabel.append(0)
					else:
						newVisitLabel.append(mapping[code])
				newPatient.append(newVisit)
				newPatientLabel.append(newVisitLabel)
			newSeqs.append(newPatient)
			newLabels.append(newPatientLabel)

		# print newLabels[0][0]
		
		return newSeqs, newLabels 

	newSeqsTrain, newLabelsTrain = genNewSeqs(seqsTrain, types, CCSMapping)
	newSeqsTest, newLabelsTest = genNewSeqs(seqsTest, types, CCSMapping)
	newSeqsValid, newLabelsValid = genNewSeqs(seqsValid, types, CCSMapping)

	print 'types size: ', len(types)

	def pickleDump(pids, dates, newSeqs, newLabels, outFile, fileExt):
		pickle.dump(pids, open(outFile+'.pids.'+fileExt, 'wb'), -1)
		pickle.dump(dates, open(outFile+'.dates.'+fileExt, 'wb'), -1)
		pickle.dump(newSeqs, open(outFile+'.visits.'+fileExt, 'wb'), -1)
		pickle.dump(newLabels, open(outFile+'.labels.'+fileExt, 'wb'), -1)

	# print newLabelsTest[0][0]
	pickleDump(pidsTrain, datesTrain, newSeqsTrain, newLabelsTrain, outFile, 'train')
	pickleDump(pidsTest, datesTest, newSeqsTest, newLabelsTest, outFile, 'test')
	pickleDump(pidsValid, datesValid, newSeqsValid, newLabelsValid, outFile, 'valid')
	
	pickle.dump(types, open(outFile+'.types', 'wb'), -1)
