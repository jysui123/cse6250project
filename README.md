# CSE 6250 Big Data for Healthcare Term Project
# ICU patient diagnosis prediction

## Author
name|email|gtid
:-:|:-:|:-:
Jingyang Sui|jysui@gatech.edu|jsui7
Qianzhen Li||
Chenyu Shi|cshi74@gatech.edu|cshi74

## Modification Based on DoctorAI
+ Use CCS label mapping to compress label space
+ Modify CCS label mapping, make some mapped integer label in original mapping smaller
+ Modify `process_mimic.py` to split input dataset to 3 folds (train, test, valid)
+ Generate time file to predict patient's next visit time 
+ Generate mortality label in `process_mimic_mortality.py` to do mortality prediction 

## Install And Usage
We use Anaconda to setup python virtual environment. To run the model, follow the steps below.
+ Create virtual environment. At the root directory of this repo, run 
```
conda env create -f env.yml
```
+ Activate virtual environment. At the root directory of this repo, run 
```
activate theano-py2-env
```
+ To generate visit label prediction and visit time prediction training/testing files, put `ADMISSION.csv`, `DIAGNOSIS_ICD.csv` from mimic-III to the root directory of this repo, then run
```
python process_mimic.py ADMISSION.csv DIAGNOSIS_ICD.csv <your output file name prefix>
```
It will automatically generate all the files (visits, labels and time file) into 3 folds with `.train`, `.test` and `.valid` suffix that matches the training requirement. It will also print the label numbers in visit file and label files, which are arguments to `doctorAI.py` for proper training.
Similarly, to generate mortality labels, run
```
python process_mimic_mortality.py ADMISSION.csv DIAGNOSIS_ICD.csv <your output file name prefix>
```
+ To train the model, run
```
python doctorAI.py <your visit file w/o suffix> <#labels in visit file> <your label file w/o suffix> <#labels in label file> <your model file name> {other optional arguments}
```
Here the visit file w/o suffix is the file name w/o `.train`, `.test` and `.valid` at the end. For example, if your process_mimic.py generate visit file named `testdata.visits.train`, `testdata.visits.test` and `testdata.visits.valid`, you should input `testdata.visits` as argument. Same rule applies for label and time files.
If you want to also predict visit time, add additional arguments in `{other optional arguments}` into the above command:
```
--predict_time 1 --time_file <your time file w/o suffix>
```
For other training arguments, use `python doctorAI.py --help` for instructions. 
For more detailed information about the format of the training files, please refer to [doctorAI readme](https://github.com/mp2893/doctorai).
+ To test the performance metric, run
```
python testDoctorAI.py <your model file name w/ .npz suffix> <your visit file w/ suffix> <your label file w/ suffix> <model RNN hidden dimension>  {other optional arguments}
```
The argument `<model RNN hidden dimension>` is one of the optional arguments to doctorAI.py for training. Use `python doctorAI.py --help` to show the default value (should be numbers enclosed by square brackets).

## For TA Testing
+ We uploaded our model file model.15.npz and the corresponding label/visit/time files. To use them, run
```
python testDoctorAI.py model.15.npz test.visits.test test.labels.test [2000] --predict_time 1 --time_file test.time.test
``` 
