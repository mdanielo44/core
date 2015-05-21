/*global $,Class,compGeneric,Singleton,compButton,LucteriosException,MINOR,SELECT_NONE,SELECT_SINGLE,SELECT_MULTI*/

var compGridHeader = Class.extend({
	name : "",
	type : "",
	label : "",

	initial : function(component) {
		this.name = component.getAttribute("name");
		this.type = component.getAttribute("type");
		this.label = component.getTextFromXmlNode();
	},

	getHtml : function() {
		return '<th>{0}</th>'.format(this.label);
	}
});

var compGridValue = Class.extend({
	name : "",
	value : "",
	parentGrid : "",

	initial : function(component) {
		this.name = component.getAttribute("name");
		this.value = component.getTextFromXmlNode();
	},

	setParentGrid : function(grid) {
		this.parentGrid = grid;
	},

	getHtml : function() {
		if (this.value === "") {
			return '<td></td>';
		}
		switch (this.parentGrid.getValueType(this.name)) {
		case 'icon':
			return '<td><img src="{0}"></td>'.format(Singleton().Transport()
					.getIconUrl(this.value));
		case 'bool':
			if ((this.value === '0') || (this.value.toLowerCase() === 'false')
					|| (this.value === 'n')) {
				return '<td>Non</td>';
			}
			return '<td>Oui</td>';
		default:
			return '<td>{0}</td>'.format(this.value
					.convertLuctoriosFormatToHtml());
		}
	}
});

var compGridRow = Class
		.extend({
			id : 0,
			values : null,
			grid : "",

			initial : function(component, grd) {
				this.grid = grd;
				this.id = component.getAttribute("id");

				var vals = component.getElementsByTagName("VALUE"), idx_val, val;
				this.values = [];
				for (idx_val = 0; idx_val < vals.length; idx_val++) {
					val = new compGridValue();
					val.initial(vals[idx_val]);
					val.setParentGrid(this.grid);
					this.values[this.values.length] = val;
				}
			},

			getHtml : function() {
				var html = '<tr id="{0}_{1}" >'.format(this.grid.name, this.id), idx_val;
				for (idx_val = 0; idx_val < this.values.length; idx_val++) {
					html += this.values[idx_val].getHtml();
				}
				html += '</tr>';
				return html;
			},

			selectGridRow : function() {
				var row = $('#{0}_{1}'.format(this.grid.name, this.id));
				if (row.hasClass("selected")) {
					row.removeClass("selected");
				} else {
					this.grid.clear_select_row();
					row.addClass("selected");
				}
				this.grid.selectChange();
			},

			dbClickRow : function() {
				this.grid.clear_select_row();
				var row = $('#{0}_{1}'.format(this.grid.name, this.id));
				row.addClass("selected");
				this.grid.dbclick();
			},

			setSelected : function(select) {
				var row = $('#{0}_{1}'.format(this.grid.name, this.id));
				if (select) {
					row.addClass("selected");
				} else {
					row.removeClass("selected");
				}
			},

			isSelected : function() {
				var row = $('#{0}_{1}'.format(this.grid.name, this.id));
				return row.hasClass("selected");
			},

			addAction : function() {
				var row = $('#{0}_{1}'.format(this.grid.name, this.id));
				row.click($.proxy(this.selectGridRow, this));
				row.dblclick($.proxy(this.dbClickRow, this));
			}

		});

var compGrid = compGeneric
		.extend({

			buttons : null,
			gridHeaders : null,
			gridRows : null,
			has_multi : false,
			page_max : 1,
			page_num : 0,

			initial : function(component) {
				this._super(component);
				this.page_max = component.getXMLAttributInt('PageMax', 1);
				this.page_num = component.getXMLAttributInt('PageNum', 0);
				var heads = component.getElementsByTagName("HEADER"), rows = component
						.getElementsByTagName("RECORD"), iChild, row, header, actions, acts, btn;

				// traitement des HEADER
				this.gridHeaders = [];
				for (iChild = 0; iChild < heads.length; iChild++) {
					header = new compGridHeader();
					header.initial(heads[iChild]);
					this.gridHeaders[this.gridHeaders.length] = header;
				}

				// traitement des RECORD
				this.gridRows = [];
				for (iChild = 0; iChild < rows.length; iChild++) {
					row = new compGridRow();
					row.initial(rows[iChild], this);
					this.gridRows[this.gridRows.length] = row;
				}

				// traitement des ACTIONS
				this.buttons = [];
				actions = component.getFirstTag("ACTIONS");
				if (actions !== null) {
					acts = actions.getElementsByTagName("ACTION");
					for (iChild = 0; iChild < acts.length; iChild++) {
						btn = new compButton(this.owner);
						btn.initial(acts[iChild]);
						btn.name = "{0}_{1}".format(this.name, iChild);
						btn.description = '';
						btn.action = Singleton().CreateAction();
						btn.action.initialize(this.owner,
								Singleton().Factory(), acts[iChild]);
						if (btn.action.mSelect === SELECT_MULTI) {
							this.has_multi = true;
						}
						this.buttons[this.buttons.length] = btn;
					}
				}
				this.selectedList = [];
			},

			addPageSelector : function() {
				var html = '', idx, opt_select,
					option_text = '<option value="{0}" {1}>' + Singleton().getTranslate("Page #") + '{2}</option>';
				if (this.page_max > 1) {
					html += "<select id='PAGE_{0}'>".format(this.name);
					for (idx = 0; idx < this.page_max; idx++) {
						opt_select = (idx === this.page_num) ? 'selected' : '';
						html += option_text.format(idx, opt_select, idx + 1);
					}
					html += "</select>";
				}
				return html;
			},

			getHtml : function() {
				var html = '<table class="grid">', iHead, iRow, iBtn;
				if (this.buttons.length === 0) {
					html += '<tr><td style="text-align: right;">';
					html += this.addPageSelector();
					html += '</td></tr>';
				}
				html += '<tr><td class="gridContent">';
				html += '<table id="{0}"><thead><tr>'.format(this.name);
				// parcours des headers
				for (iHead = 0; iHead < this.gridHeaders.length; iHead++) {
					html += this.gridHeaders[iHead].getHtml();
				}
				html += '</tr></thead><tbody>';
				// parcours des rows
				for (iRow = 0; iRow < this.gridRows.length; iRow++) {
					html += this.gridRows[iRow].getHtml();
				}
				html += '</tbody></table>';

				html += '</td>';

				if (this.buttons.length > 0) {
					html += '<td class="gridActions" id="' + this.name
							+ '_actions">';
					html += this.addPageSelector();
					// parcours des boutons
					for (iBtn = 0; iBtn < this.buttons.length; iBtn++) {
						html += this.buttons[iBtn].getHtml();
					}
					html += '</td>';
				}

				html += '</tr></table>';
				return html;
			},

			getSelectedId : function() {
				var selectedList = [], iRow;
				for (iRow = 0; iRow < this.gridRows.length; iRow++) {
					if (this.gridRows[iRow].isSelected()) {
						selectedList.push(this.gridRows[iRow].id);
					}
				}
				return selectedList;
			},

			selectChange : function() {
				var selectedList = this.getSelectedId(), select_type, iBtn;
				if (selectedList.length === 0) {
					select_type = SELECT_NONE;
				} else if (selectedList.length === 1) {
					select_type = SELECT_SINGLE;
				} else {
					select_type = SELECT_MULTI;
				}
				for (iBtn = 0; iBtn < this.buttons.length; iBtn++) {
					this.buttons[iBtn].setSelectType(select_type);
				}
			},

			clear_select_row : function() {
				if (!this.has_multi) {
					var iRow;
					for (iRow = 0; iRow < this.gridRows.length; iRow++) {
						this.gridRows[iRow].setSelected(false);
					}
				}
			},

			getValueType : function(name) {
				var iCol;
				for (iCol = 0; iCol < this.gridHeaders.length; iCol++) {
					if (this.gridHeaders[iCol].name === name) {
						return this.gridHeaders[iCol].type;
					}
				}
				// ne devrait jamais arriver mais par defaut, on retourne 'str'
				return 'str';
			},

			addAction : function() {
				var iRow, iBtn, select_name;
				for (iRow = 0; iRow < this.gridRows.length; iRow++) {
					this.gridRows[iRow].addAction();
				}
				for (iBtn = 0; iBtn < this.buttons.length; iBtn++) {
					this.buttons[iBtn].addAction();
					this.buttons[iBtn].setSelectType(SELECT_NONE);
				}
				select_name = 'PAGE_{0}'.format(this.name);
				if ($("#" + select_name).length) {
					$("#" + select_name).change(
							$.proxy(function() {
								var page_val = $("#" + select_name).val();
								this.owner.getContext().put(
										'GRID_PAGE%25{0}'.format(this.name),
										page_val);
								this.owner.getContext().put(
										'GRID_PAGE%{0}'.format(this.name),
										page_val);
								this.owner.refresh();
							}, this));
				}
			},

			dbclick : function() {
				if ((this.buttons.length > 0) && (this.getSelectedId() > 0)) {
					this.selectChange();
					this.buttons[0].actionPerformed();
				}
			},

			getValue : function() {
				var selectedList = this.getSelectedId();
				return selectedList.join(';');
			},

			initialVal : function() {
				return '';
			},

			setValue : function(xmlValue) {
				this.initial(xmlValue.parseXML());
				this.getGUIComp().html(this.getHtml());
			},

			fillValue : function(params) {
				var with_gridval = false, is_multi = false, iBtn;
				for (iBtn = 0; iBtn < this.buttons.length; iBtn++) {
					if ((this.buttons[iBtn].hasBeenClicked)
							&& (this.buttons[iBtn].btnaction.mSelect !== SELECT_NONE)) {
						with_gridval = true;
						is_multi = (this.buttons[iBtn].btnaction.mSelect === SELECT_MULTI);
					}
				}
				if (with_gridval) {
					if (this.getValue() === '') {
						throw new LucteriosException(MINOR, Singleton()
								.getTranslate("Select one line before!"));
					}
					if (!is_multi && (this.getSelectedId().length > 1)) {
						throw new LucteriosException(MINOR, Singleton()
								.getTranslate("Select only one line!"));
					}
					params.put(this.name, this.getValue());
				}
			}

		});
