zip:
	rm -f l5pc_nsg.zip
	rm -rf zipcontent
	mkdir -p zipcontent
	cp init.py zipcontent
	cp -r ../config ../morphology ../opt_l5pc.py ../l5pc_model.py ../l5pc_evaluator.py ../checkpoints/checkpoint.pkl zipcontent
	cp ../mechanisms/*.mod zipcontent
	zip -r l5pc_nsg.zip zipcontent
