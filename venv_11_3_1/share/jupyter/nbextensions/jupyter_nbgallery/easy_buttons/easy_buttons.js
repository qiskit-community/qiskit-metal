define([
  'jquery',
  'base/js/namespace',
  'services/config',
  'base/js/utils'
], function(
  $,
  jupyter,
  configmod,
  utils
) {
  function load_ipython_extension() {
    var config = new configmod.ConfigSection('common', {base_url: utils.get_body_data("baseUrl")});
    config.load();
  
    config.loaded.then(function(){
      var easy_buttons = config['data'].nbgallery.easy_buttons;
      if(easy_buttons == true){ 
          // attach function to focusing
        $(jupyter.events).on('select.Cell', function (event, data) {
          add_buttons();
        });
        $(jupyter.events).on('edit_mode.Cell',  function (event, data) {
          add_buttons();
        });
        $(jupyter.events).on('command_mode.Cell',  function (event, data) {
          add_buttons();
        });
      }
    });
  
    ///////////////////////////////////////////////////////////////////////////////////////////////////
    //////////////////                 add 'easy buttons' in        ///////////////////////////////////
    ///////////////////////////////////////////////////////////////////////////////////////////////////
    var add_buttons =  function() {
      // on init remove toolbar
      //$('#maintoolbar').hide();
      //$('#header-container').hide();
      // maybe put these buttons in the 'celltoolbar'
      var cells = Jupyter.notebook.get_cells();
      for (var i = 0; i < cells.length; i++){
        var cell = cells[i];
        var  div = cell.element.find('.inner_cell')
        //console.log(div);
        if (cell.selected){
          //show buttons
           if (Jupyter.notebook.get_selected_cell().element.find('.simple_run').length == 0){
             var button_container = $(div)
             var button_div = $('<div/>').addClass('simple_run').show().css({
               'margin-top':'-17px',
               'background-color':'white'
             });
              // let's create a button that shows the current value of the metadata
              //<button class="btn btn-default" title="run cell, select below" 
              // data-jupyter-action="jupyter-notebook:run-cell-and-select-next"><i class="fa-step-forward fa"></i></button>
  
            var button_cell_run  = $('<button/>').addClass('btn btn-default').addClass('fa-play fa').text(' Run').css({
              'width': '8%', 
              'margin-left':'2px',
              'background-color': 'rgb(119, 195, 127)', 
              'border-radius': '3px', 
            });
  
            var button_cell_run_below  = $('<button/>').addClass('btn btn-default').addClass('fa-fast-forward fa').text(' Run All').css({
              'width': '8%', 
              'margin-left':'2px',
              'background-color': 'rgb(119, 195, 127)', 
              'border-radius': '3px', 
            }); //Run me and everything below
  
            // add method to only show the aplicable button
            var button_cell_markdown  = $('<button/>').addClass('btn btn-default').addClass('fa-font fa').text(' Markdown').css({
              'margin-left':'6%',
              'width': '10%',
              'border-radius': '3px', 
              });
              
            var button_cell_code  = $('<button/>').addClass('btn btn-default').addClass('fa-terminal fa').text(' Code').css({
              'width': '6%',
              'border-radius': '3px', 
            });
  
            var button_cell_below = $('<button/>').addClass('btn btn-default').addClass('fa-arrow-down fa').text(' Insert Below').css({
              'margin-left':'7%',
              'width': '12%',
              'border-radius': '3px', 
            });
            
            var button_cell_above = $('<button/>').addClass('btn btn-default').addClass('fa-arrow-up fa').text(' Insert Above').css({
              'width': '12%',
              'border-radius': '3px', 
            });
  
            var button_cell_delete = $('<button/>').addClass('btn btn-default').addClass('fa-trash fa').text(' Delete').css({
              'margin-left':'10%',
              'width': '10%',
              'background-color': 'rgba(239, 14, 14, 0.55)',
              'border-radius': '3px', 
            });
  
            var button_cell_restart  = $('<button/>').addClass('btn btn-default').addClass('fa-repeat fa').text(' Restart').css({
              'width': '10%',
              'border-radius': '3px', 
            });
  
            // On click, insert cell above
            button_cell_above.click(function(){  Jupyter.notebook.insert_cell_above()            })
  
            // On click, insert cell below
            button_cell_below.click(function(){  Jupyter.notebook.insert_cell_below() });
  
            // On click, delete cell
            button_cell_delete.click(function(){  Jupyter.notebook.delete_cell()  });
  
            // On click, run / run all below
            button_cell_run.click(function(){  Jupyter.notebook.execute_cell() });
            button_cell_run_below.click(function(){  Jupyter.notebook.execute_cells_below() });
  
            // On click, insert cell below
            button_cell_markdown.click(function(){  Jupyter.notebook.to_markdown() });
  
            // On click, insert cell below
            button_cell_code.click(function(){  Jupyter.notebook.to_code() });
  
            // On click, insert cell below
            button_cell_restart.click(function(){  Jupyter.notebook.restart_kernel() });
  
            // add the button to the div.
            button_div.append(button_cell_run);
            button_div.append(button_cell_run_below);
            button_div.append(button_cell_markdown);
            button_div.append(button_cell_code);
            button_div.append(button_cell_below);
            button_div.append(button_cell_above);
            button_div.append(button_cell_delete);
  
            button_div.append(button_cell_restart);
            button_container.prepend(button_div);
          }
        $(div).find('.simple_run').show();
        } else{
          // make sure buttons are hidden
          $(div).find('.simple_run').hide();
        }
      }
    };
  }
  return {load_ipython_extension : load_ipython_extension};
});
