# CSE 6250 Big Data for Healthcare Term Project
# ICU patient diagnosis prediction

## Author
name|email|gtid
:-:|:-:|:-:
Jingyang Sui|jysui@gatech.edu|jsui7
Qianzhen Li||
Chenyu Shi||

## Modification Based on DoctorAI
+ Use CCS label mapping to compress label space
+ Modify CCS label mapping, make some mapped integer label in original mapping smaller
+ Modify `process_mimic.py` to split input dataset to 3 folds (train, test, valid)

## TODO
- Understand evaluation methods (`testDoctorAI.py` and original paper)
- Generate time file to predict patient visit date
- Change the label to be mortality and try to predict mortality
- Project (video, code, report) DUE on 04/28