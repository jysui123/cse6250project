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
    return 'D_' + convert_to_icd9(dxStr)

def dt_to_integer(dt_time, precision='day'):
	div = 1
	if precision == 'second':
		div = 1
	elif precision == 'minute':
		div = 100
	elif precision == 'hour':
		div = 10000
	elif precision == 'day':
		div = 1000000
	elif precision == 'month':
		div = 100000000
	elif precision == 'year':
		div = 10000000000
	else:
		print 'ERROR: wrong precision level'
		exit(0)
	intTime = dt_time.year*10000000000+dt_time.month*100000000+dt_time.day*1000000+dt_time.hour*10000+dt_time.minute*100+dt_time.second
	return intTime//div

if __name__ == '__main__':
	admissionFile = sys.argv[1]
	diagnosisFile = sys.argv[2]
	outFile = sys.argv[3]

	# label file location
	PATH_LABELMAP = "labelMap.csv"
	df_map = pd.read_csv("labelMap.csv", usecols=["code", "cat"])
	df_map["code"] = df_map["code"].apply(convert_to_label)
	CCSMapping = dict(zip(df_map.code, df_map.cat))

	print 'CCSMapping items:', len(CCSMapping)

	print 'Building pid-admission mapping, admission-date mapping'
	pidAdmMap = {}
	admDateMap = {}
	pidMortMap = {}
	infd = open(admissionFile, 'r')
	infd.readline()
	for line in infd:
		tokens = line.strip().split(',')
		pid = int(tokens[1])
		admId = int(tokens[2])
		deathTime = tokens[5]
		if len(deathTime) == 0:
			pidMortMap[pid] = 0
		else:
			pidMortMap[pid] = 1
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
	timeTrain = []
	timeTest = []
	timeValid = []
	datesIntTrain = []
	datesIntTest = []
	datesIntValid = []
	mortTrain = []
	mortTest = []
	mortValid = []
	i = 0

	def appendToList(pid, visits, pids, dates, datesInt, seqs, times):
		pids.append(pid)
		seq = []
		date = []
		time = [0]
		dateInt = []
		for i, visit in enumerate(visits):
			date.append(visit[0])
			dateInt.append(dt_to_integer(visit[0]))
			seq.append(visit[1])
			if i > 0:
				time.append(dt_to_integer(visits[i][0])-dt_to_integer(visits[i-1][0]))
		dates.append(date)
		seqs.append(seq)
		datesInt.append(dateInt)
		times.append(time)

	# split the data into train, test, valid sets, with ratio of 8:1:1
	for pid, visits in pidSeqMap.iteritems():
		if i < 8:
			appendToList(pid, visits, pidsTrain, datesTrain, datesIntTrain, seqsTrain, timeTrain)
		elif i < 9:
			appendToList(pid, visits, pidsTest, datesTest, datesIntTest, seqsTest, timeTest)
		else:
			appendToList(pid, visits, pidsValid, datesValid, datesIntValid, seqsValid, timeValid)	
		i = (i+1)%10
	
	print 'Converting strSeqs to intSeqs, and making types'
	types = {}
	mappedTypes = set()
	mappedTypesWith0 = set()
	startingIndex = 297

	notMatch = 0

	def genNewSeqs(seqs, types, mapping, mappedTypes, mappedTypesWith0):
		newSeqs = []
		newLabels = []

		notMatch = 0
		
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
						mappedTypes.add(code)
						mappedTypesWith0.add(0)
						notMatch = notMatch + 1
					else:
						newVisitLabel.append(mapping[code])
						mappedTypes.add(mapping[code])
						mappedTypesWith0.add(mapping[code])
				newPatient.append(newVisit)
				newPatientLabel.append(newVisitLabel)
			newSeqs.append(newPatient)
			newLabels.append(newPatientLabel)

		# print newLabels[0][0]
		return newSeqs, newLabels, notMatch

	newSeqsTrain, newLabelsTrain, nm = genNewSeqs(seqsTrain, types, CCSMapping, mappedTypes, mappedTypesWith0)
	notMatch = notMatch + nm
	newSeqsTest, newLabelsTest, nm = genNewSeqs(seqsTest, types, CCSMapping, mappedTypes, mappedTypesWith0)
	notMatch = notMatch + nm
	newSeqsValid, newLabelsValid, nm = genNewSeqs(seqsValid, types, CCSMapping, mappedTypes, mappedTypesWith0)
	notMatch = notMatch + nm

	print 'not matched diagnosis: ', notMatch
	print 'mapped types:', len(mappedTypes)
	print 'types size: ', len(types)
	print 'mapped types w/ 0:', len(mappedTypesWith0)

	mappedTypeSet = set()
	maxCodeNum = 0
	for k, v in CCSMapping.iteritems():
		mappedTypeSet.add(v)
		if v > maxCodeNum:
			maxCodeNum = v
	print 'mapped types in CCSMapping:', len(mappedTypeSet)
	print mappedTypeSet

	n_mort = 0
	print "n patients", len(pidMortMap)
	for pid, mort in pidMortMap.iteritems():
		if mort == 1:
			n_mort = n_mort + 1
	print "n dead", n_mort

	def mortLabels(pidMortMap, newLabels, pids):
		mortLabels = []
		for i, pid in enumerate(pids):
			mortLabel = []
			for labels in newLabels[i]:
				mort = []
				for label in labels:
					if pidMortMap[pid] == 0:
						mort.append(0)
					else:
						mort.append(1)
				mortLabel.append(mort)
			mortLabels.append(mortLabel)
		return mortLabels

	mortLabelsTrain = mortLabels(pidMortMap, newLabelsTrain, pidsTrain)
	mortLabelsTest = mortLabels(pidMortMap, newLabelsTest, pidsTest)
	mortLabelsValid = mortLabels(pidMortMap, newLabelsValid, pidsValid)

	# for i, labels in enumerate(mortLabelsTrain):
	# 	if i > 5:
	# 		break
	# 	print labels

	def pickleDump(pids, dates, newSeqs, newLabels, times, outFile, fileExt):
		pickle.dump(pids, open(outFile+'.pids.'+fileExt, 'wb'), -1)
		pickle.dump(dates, open(outFile+'.dates.'+fileExt, 'wb'), -1)
		pickle.dump(newSeqs, open(outFile+'.visits.'+fileExt, 'wb'), -1)
		pickle.dump(newLabels, open(outFile+'.labels.'+fileExt, 'wb'), -1)
		pickle.dump(times, open(outFile+'.time.'+fileExt, 'wb'), -1)

	# print newLabelsTest[0][0]
	pickleDump(pidsTrain, datesTrain, newSeqsTrain, mortLabelsTrain, timeTrain, outFile, 'train')
	pickleDump(pidsTest, datesTest, newSeqsTest, mortLabelsTest, timeTest, outFile, 'test')
	pickleDump(pidsValid, datesValid, newSeqsValid, mortLabelsValid, timeValid, outFile, 'valid')
	
	pickle.dump(types, open(outFile+'.types', 'wb'), -1)

	print '***************************'
	print '* arguments to doctorAI.py:'
	print '* number of codes in visit file:', len(types)
	print '* number of codes in label file:', maxCodeNum + 1
	print '***************************'
