zip:
	cd .. && \
		zip -r nsg/l5pc_nsg.zip config/ morphology/ opt_l5pc.py l5pc_model.py l5pc_evaluator.py checkpoints/checkpoint.pkl
	cd ../mechanisms && \
		zip -r ../nsg/l5pc_nsg.zip *.mod
	zip -u l5pc_nsg.zip init.py
