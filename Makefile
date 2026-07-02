.PHONY: reproduce reproduce-data reproduce-paper paper validate test

reproduce: reproduce-data reproduce-paper

reproduce-data:
	pixi run prepare-kvasir
	pixi run prepare-hyperkvasir
	pixi run prepare-colonoscopy-3class

reproduce-paper:
	python3 scripts/generate_paper_tables.py
	$(MAKE) -C docs/paper all

paper:
	$(MAKE) -C docs/paper all

validate:
	bash scripts/validate_publication.sh all

test:
	pixi run python -c "import tests.test_prepare_colonoscopy_3class as t; t.test_group_split_keeps_groups_disjoint(); t.test_infer_group_id_for_video_frames()"
	pixi run python -m pytest tests/ -q
