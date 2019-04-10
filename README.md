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
- Understand evaluation methods (testDoctorAI.py and original paper)
- Tune parameters of doctorAI.py to achieve better performance
- Write a plot script
- Draft DUE on 04/14