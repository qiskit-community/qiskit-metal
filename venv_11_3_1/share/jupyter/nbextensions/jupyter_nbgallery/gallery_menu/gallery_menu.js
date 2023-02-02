$.ajaxSetup({ xhrFields: { withCredentials: true } });

define([
  'jquery',
  'base/js/utils',
  'services/config',
  'nbextensions/jupyter_nbgallery/gallery_menu/bootbox.min'
], function(
  $,
  utils,
  configmod,
  bootbox
){
  function load_ipython_extension() {
    var config = new configmod.ConfigSection('common',{base_url: utils.get_body_data("baseUrl")});
    config.load();
    
    config.loaded.then(function() {
      // 'base' is the "home" nbgallery that's configured for this Jupyter instance
      base = config['data'].nbgallery.url;

      // 'notebook_base' is the gallery this notebook was launched from
      var gallery_metadata = Jupyter.notebook.metadata.gallery;
      var notebook_base = base;
      if (gallery_metadata && gallery_metadata.gallery_url) {
        notebook_base = gallery_metadata.gallery_url;
      }
  
      var gallery_menu = $('<li>').addClass('dropdown');
      var gallery_preferences_menu = $('<li>').addClass('dropdown');
      var shortcuts = Jupyter.keyboard_manager.command_shortcuts._shortcuts; 
      
      var build_gallery_preferences_menu = function(){
        gallery_preferences_menu.empty();
        gallery_preferences_menu.append('<a class="dropdown-toggle" data-toggle="dropdown">Preferences</a>');
        
        var links = $('<li>');
        links.append('<a href="#" id="prefs_autoCloseBrackets">Auto Close Brackets</a>');
        links.append('<a href="#" id="prefs_smartIndent">Smart Indent</a>');
        links.append('<a href="#" id="prefs_indent_width">Indent Width</a>');
        links.append('<a href="#" id="prefs_easy_buttons">Easy Buttons</a>');

        gallery_preferences_menu.append($('<ul>').addClass('dropdown-menu').append(links));

        var update_preferences = function(preference,value, type){
          if (type=='notebook'){
            var config = new configmod.ConfigSection('notebook',{base_url:utils.get_body_data("baseUrl")});
            config.load();
            config.loaded.then(function(){
              var update_cm_config = {};
              update_cm_config[preference]=value;
              config.update({'CodeCell':{'cm_config':update_cm_config}});
              var code_config = config['data'].CodeCell.cm_config;
              var cells = Jupyter.notebook.get_cells();
              for (var i in cells){
                var c = cells[i];
                if(c.cell_type === 'code'){
                  for(setting in code_config){
                    c.code_mirror.setOption(setting, code_config[setting]);
                  }
                }
              }
            });
          }
          else if(type=='common'){
            var config = new configmod.ConfigSection('common',{base_url: utils.get_body_data("baseUrl")});
            config.load();
            config.loaded.then(function(){
              config.update({nbgallery:{easy_buttons:value}});
            });
          }

          var data = {};
          data[preference] = value;
            
          $.ajax({
            method: 'POST',
            headers:{
              Accept: 'application/json'
            },
            url: base + '/preferences', 
            data: data,
            xhrFields: { withCredentials: true }
          });
        }
      
        $('#prefs_autoCloseBrackets').on('click',function(){
          bootbox.dialog({
            title: 'Auto Close Brackets?',
            message: "Would you like this Jupyter instance to automatically provide a closing bracket or paraenthesis whenever you type an opening one?",
            buttons: {
              yes: {
                label: "Of course!",
                className: 'btn-primary',
                callback: function(){ update_preferences('autoCloseBrackets',true, 'notebook') }
              },
              no: {
                label: "Nah I'm good",
                callback: function(){ update_preferences('autoCloseBrackets',false, 'notebook') }
              }
            }
          });
        });

        $('#prefs_smartIndent').on('click',function(){
          bootbox.dialog({
            title: 'Smart Indent?',
            message: "Would you like this Jupyter instance to automatically try to properly indent each line?",
            buttons: {
              yes: {
              label: "Of course!",
                className: 'btn-primary',
                callback: function() { update_preferences('smartIndent',true, 'notebook') }
              },
              no: {
                label: "Nah I'm good",
                callback: function() { update_preferences('smartIndent',false, 'notebook') }
              }
            }
          });
        });

        $('#prefs_indent_width').on('click', function(){
          bootbox.dialog({
            title: 'Indent Width?',
            message: 'Do you prefer the regular 2 spaces as the indent width or are you one of those crazy people who prefer 4? The default is 2',
            buttons: {
              yes: {
                label: "I'm normal (2 spaces)",
                className: 'btn-primary',
                callback: function(){
                update_preferences('indentUnit',2,'notebook');
                update_preferences('tabSize',2,'notebook');
                }
              },
              no: {
                label: "Crazy like a fox (4 spaces)",
                callback: function(){
                update_preferences('indentUnit',4,'notebook');
                update_preferences('tabSize',4,'notebook');
                }
              }
            }
          });
        });

        $('#prefs_easy_buttons').on('click',function(){
          bootbox.dialog({
            title: 'Easy Buttons?',
            message: "What do you think of those easy buttons that appear everytime you click on a cell?  Do you want to keep them turned on (which is the default) or would you like to turn them off?",
            buttons: {
              yes: {
                label: 'Leave them on!',
                className: 'btn-primary',
                callback: function(){ update_preferences('easy_buttons', true, 'common')}
              },
              no: {
                label: 'Nope - turn them off!',
                callback: function(){ update_preferences('easy_buttons',false,'common')}
              }
            }
          });
        });
        
      }

      var build_gallery_menu = function(options) {
        gallery_menu.empty();
        gallery_menu.append('<a class="dropdown-toggle" data-toggle="dropdown">Gallery</a>');

        var links = $('<li>');
        var metadata = Jupyter.notebook.metadata.gallery;
        var linked = metadata != undefined && metadata.link != undefined;
        var cloned = metadata != undefined && metadata.clone != undefined;

        if ((linked || cloned) && (base != notebook_base)) {
          links.append('<i>&nbsp;' + notebook_base + '</i>');
        }

        if (linked && !cloned) {
          links.append('<a href="#" id="gallery_save">Save Changes to Gallery</a>');
          links.append('<a href="#" id="gallery_change_request">Submit Change Request</a>');
          links.append('<a href="#" id="gallery_upload">Upload as New Notebook (Fork)</a>');           
          links.append('<a href="#" id="gallery_unlink">Unlink from Gallery</a>');      
        } 

        if (cloned && !linked){
          links.append('<a href="#" id="gallery_change_request">Submit Change Request</a>');
          links.append('<a href="#" id="gallery_upload">Upload as New Notebook (Fork)</a>');      
          links.append('<a href="#" id="gallery_unlink">Unlink from Gallery</a>');
        } 
        
        if (!cloned && !linked) {
          links.append('<a href="#" id="gallery_upload">Upload to Gallery</a>');
          links.append('<a href="#" id="gallery_link">Link to existing notebook</a>');
        }

        if (linked || cloned) {
          links.append('<a href="#" id="gallery_update">Check for changes</a>'); 
          links.append('<li class="divider">');
          
          var href = notebook_base + "/notebooks/";
          
          if (linked)
            href += metadata.link;
          else
            href += metadata.clone;
          
          links.append('<a href="' + href +'" target="_blank">Open in the Gallery</a>');
        } else {
          // Not linked or cloned i.e. not attached to a Gallery
          links.append('<li class="divider">');
          links.append('<a href="' + base + '" target="_blank"><i class="fa fa-external-link menu-icon pull-right"></i>Visit the Gallery</a>');
        }

        gallery_menu.append($('<ul>').addClass('dropdown-menu').append(links));

        var strip_output = function(notebook) {
          var notebook_json = notebook.toJSON();
          for (i in notebook_json.cells) {
            if (notebook_json.cells[i].cell_type == 'code') {
              notebook_json.cells[i].outputs = [];
              notebook_json.cells[i].execution_count = null;
            } else {
              // 'outputs' is only allowed on code blocks but we were previously
              // setting it to [] for everything - fix by deleting here if needed.
              if (notebook_json.cells[i].outputs != undefined) {
                delete notebook_json.cells[i].outputs;
              }
            }
          }
          return notebook_json;
        }
        
        var unlink = function() {
          Jupyter.keyboard_manager.command_shortcuts.clear_shortcuts();
          
          bootbox.confirm('Are you sure you want to unlink this notebook?', function(confirmed) {
            Jupyter.keyboard_manager.command_shortcuts._shortcuts = shortcuts;
            
            if (confirmed) {
              var metadata = Jupyter.notebook.metadata.gallery;
              
              if(metadata != undefined) {
                Jupyter.notebook.metadata.gallery = { commit: metadata.commit };
                Jupyter.notebook.save_notebook();
              } else {
                Jupyter.notebook.metadata.gallery = {};
                Jupyter.notebook.save_notebook();
              }
              
              // Reset back to the home gallery
              notebook_base = base;

              build_gallery_menu();
              Jupyter.notification_area.get_widget("notebook").set_message("Notebook unlinked", 3000);
            }
          });
        };
        
        var fetch_error = function(id) {
          bootbox.dialog({
            title: 'Gallery Communication Error',
            message: "There was an error fetching information for <b>" + id + "</b>. This can happen for a few reasons:<br><br><li style='margin-left:50px'><a target='_blank' href='" + notebook_base +"'>Notebook Gallery</a> is down</li><li style='margin-left:50px'>The remote notebook was deleted</li><li style='margin-left:50px'>The remote notebook was made private</li><li style='margin-left:50px'>Your permissions on the remote notebook changed</li><br>You can try waiting it out. If this error persists, we recommend unlinking the notebook and either re-linking or uploading a new copy.",
            buttons: {
              download: {
                label: "Unlink",
                className: 'btn-danger',
                callback: unlink
              },
              cancel: {
                label: 'OK'
              }
            }
          });
        };
        
        var update_gallery_metadata = function(response) {
          if (!Jupyter.notebook.metadata.gallery) {
            Jupyter.notebook.metadata.gallery = {}
          }
          Jupyter.notebook.metadata.gallery.commit = response.commit;
          Jupyter.notebook.metadata.gallery.staging_id = response.staging_id;
          Jupyter.notebook.metadata.gallery.filename = response.filename;
          if (response.link) {
            Jupyter.notebook.metadata.gallery.link = response.link;
          } else {
            Jupyter.notebook.metadata.gallery.clone = response.clone;
          }
        };

        var save_notebook = function() {
          bootbox.dialog({
            title: 'Saving ...',
            message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
          });
          
          $.ajax({
            method: 'POST', 
            url: notebook_base + '/stages' + '?id=' + metadata.link + '&agree=yes',
            dataType: 'json',
            contentType: 'text/plain',
            headers:{
                Accept: 'application/json'
            },
            data: JSON.stringify(strip_output(Jupyter.notebook)),
            success: function(response) {
              bootbox.hideAll();
              update_gallery_metadata(response);
              Jupyter.notebook.save_notebook();
              window.open(notebook_base + "/notebook/" + response.link +"?staged=" + response['staging_id'] + "#UPDATE", '_blank');
              Jupyter.notification_area.get_widget("notebook").set_message("Notebook saved", 3000);
            },
            error: function() {
              bootbox.hideAll();
              fetch_error('the staged notebook');
            }
          });
        };
        
        
        var gallery_change_request = function() {
          bootbox.dialog({
            title: 'Submitting Change Request ...',
            message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
          });
          if (metadata.link){
             id=metadata.link;
          } else if (metadata.clone) {
            id = metadata.clone;
          }
          $.ajax({
            method: 'POST', 
            url: notebook_base + '/stages?id=' + id + '&agree=yes',
            dataType: 'json',
            contentType: 'text/plain',
            headers:{
                Accept: 'application/json'
            },
            data: JSON.stringify(strip_output(Jupyter.notebook)),
            success: function(response) {
              bootbox.hideAll();
              window.open(notebook_base + "/notebooks/" + id +"?staged=" + response['staging_id'] + "#CHANGE_REQ", '_blank'); 
              Jupyter.notification_area.get_widget("notebook").set_message("Change Request Submitted", 3000);
            },
            error: function() {
              bootbox.hideAll();
              fetch_error('the staged notebook');
            }
          });
        };
        
        var check_for_update = function(callback) {
          var gallery = Jupyter.notebook.metadata.gallery;
          
          if (linked) {
            var id = gallery.link;
          } else {
            var id = gallery.clone;
          }
          
          var seconds = new Date().getTime() /1000;
          $.ajax({
            method: 'GET', 
            url: notebook_base + '/notebooks/' + id + '/metadata?seconds=' + seconds,
            headers:{
                Accept: 'application/json'
            },        
            success: function(metadata) {
              if (metadata.commit_id != gallery.commit) {
                var buttons = {
                  cancel: {
                    label: 'Cancel'
                  },
                  diff:{
                    label: "View Diffs",
                    className:'btn-primary',
                    callback: function(){
                      bootbox.dialog({
                        title: 'Loading Diffs ...',
                        message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
                      });
                      
                     $.ajax({
                        method: 'POST', 
                        url: notebook_base + '/notebooks/' + id + '/diff',
                        dataType: 'json',
                        contentType: 'text/plain',
                        headers:{
                            Accept: 'application/json'
                        },
                        data: JSON.stringify(strip_output(Jupyter.notebook)),
                        success: function(response) {
                          var diff_buttons ={
                            cancel: {
                              label: 'Cancel'
                            },
                            download: {
                              label: "Download and replace <b>local</b>",
                              className: 'btn-warning',
                              callback: function() {
                                bootbox.dialog({
                                  title: 'Downloading ...',
                                  message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
                                });
                                
                                $.ajax({
                                  url: notebook_base + '/notebooks/' + id + '/download',
                                  error: function(e) {
                                    bootbox.hideAll();
                                    fetch_error(id);
                                  },
                                  success: function(content) {
                                    Jupyter.notebook.fromJSON({
                                      type: "notebook", 
                                      path: Jupyter.notebook.notebook_path,
                                      name: Jupyter.notebook.notebook_name,
                                      content: JSON.parse(content)
                                    });
                                    bootbox.hideAll();
                                    Jupyter.notification_area.get_widget("notebook").set_message("Notebook updated", 3000);
                                  }
                                });
                              }
                            }                        
                          }
                          if (linked) {
                            diff_buttons['upload'] = {
                              label: "Upload and replace <b>remote</b>",
                              className: 'btn-danger',
                              callback: save_notebook
                            }
                          }
                          bootbox.hideAll();
                          bootbox.dialog({
                            message: response['css'] + response['inline'],
                            onEscape: true,
                            buttons: diff_buttons
                          }).find('.modal-dialog').css({'width':'85%'}).find('.modal-content').css({'overflow-y':'auto','height':'60em'});
                        },
                        error: function() {
                          bootbox.hideAll();
                          fetch_error('the staged notebook');
                        }
                      });
                     
                    }
                  },
                  download: {
                    label: "Download and replace <b>local</b>",
                    className: 'btn-warning',
                    callback: function() {
                      bootbox.dialog({
                        title: 'Downloading ...',
                        message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
                      });
                      
                      $.ajax({
                        url: notebook_base + '/notebooks/' + id + '/download',
                        error: function() {
                          bootbox.hideAll();
                          fetch_error(id);
                        },
                        success: function(content) {
                          Jupyter.notebook.fromJSON({
                            type: "notebook", 
                            path: Jupyter.notebook.notebook_path,
                            name: Jupyter.notebook.notebook_name,
                            content: JSON.parse(content)
                          });
                          bootbox.hideAll();
                          Jupyter.notification_area.get_widget("notebook").set_message("Notebook updated", 3000);
                        }
                      });
                    }
                  }
                }
                
                if (linked) {
                  buttons['upload'] = {
                    label: "Upload and replace <b>remote</b>",
                    className: 'btn-danger',
                    callback: save_notebook
                  }
                }
          
                bootbox.dialog({
                  title: 'Remote notebook changed',
                  message: "The <a target='_blank' href='" + notebook_base + "/notebooks/" + id + "'>remote notebook</a> has changed since you checked it out. What would you like to do?",
                  buttons: buttons
                });
              } else {
                if (callback != undefined) {
                  callback()
                }
              }
            },
            error: function() {
              fetch_error(id);
            }
          });
        };
        
        $('#gallery_save').click(function() {
          check_for_update(save_notebook);
        });
        
        $('#gallery_change_request').click(function() {
          gallery_change_request();
        });
        
        
        $('#gallery_update').click(function() {
          check_for_update(function() {
            bootbox.alert('No changes have been made to the remote notebook');
          });
        });
        
        $('#gallery_link').click(function() {
          Jupyter.keyboard_manager.command_shortcuts.clear_shortcuts();

          bootbox.prompt('Enter notebook URL', function(nb_url) {
            // Set notebook base from the new link url
            var url = new URL(nb_url);
            notebook_base = url.origin;
            Jupyter.keyboard_manager.command_shortcuts._shortcuts = shortcuts;
            var seconds = new Date().getTime() /1000;
            $.ajax({
              method: 'GET',
              url: nb_url + '/uuid?seconds=' + seconds,
              success: function(id){
                if (id != null) {
                  $.ajax({
                    method: 'GET', 
                    url: notebook_base + '/notebooks/' + id.uuid + '/metadata?seconds=' + seconds, 
                    success: function(metadata) {
                      Jupyter.keyboard_manager.command_shortcuts._shortcuts = shortcuts;
                      // Fill in Gallery metadata
                      // TODO: Add check to see if they can edit, that determines if it gets a link or clone id
                      Jupyter.notebook.metadata.gallery = { 
                        gallery_url: notebook_base,
                        link: id.uuid,
                        commit:  metadata.commit_id
                      };
                      Jupyter.notebook.save_notebook();
                      build_gallery_menu();
                      Jupyter.notification_area.get_widget("notebook").set_message("Notebook linked", 3000);
                    },
                    error: function() {
                      Jupyter.keyboard_manager.command_shortcuts._shortcuts = shortcuts;
                      fetch_error(id);
                    }
                  });
                }
              } 
            })
          });
        });
        
        $('#gallery_unlink').click(unlink);
        
        $('#gallery_upload').click(function() {
          bootbox.dialog({
            title: 'Uploading ...',
            message: '<div class="progress progress-striped active"><div class="progress-bar"  role="progressbar" aria-valuenow="45" aria-valuemin="0" aria-valuemax="100" style="width: 100%">'
          });

          $.ajax({
            method: 'POST', 
            url: notebook_base + '/stages?agree=yes',
            dataType: 'json',
            contentType: 'text/plain',
            headers:{
                Accept: 'application/json'
            },
            data: JSON.stringify(strip_output(Jupyter.notebook)),
            success: function(response) {
              bootbox.hideAll();
              update_gallery_metadata(response);
              Jupyter.notebook.save_notebook();
              window.open(notebook_base + "/notebooks/?staged=" + response['staging_id'] +"#STAGE", '_blank');
              build_gallery_menu();
              Jupyter.notification_area.get_widget("notebook").set_message("Notebook uploaded", 3000);
            },
            error: function() {
              bootbox.hideAll();
              fetch_error('the staged notebook');
            }
          });
        });
        
        if ((linked || cloned) && (options != undefined && options.check_for_update)) {
          check_for_update();
        }
      }
      
      $('ul.nav.navbar-nav').append(gallery_menu);
      $('ul.nav.navbar-nav').append(gallery_preferences_menu);
      build_gallery_menu({check_for_update:true});
      build_gallery_preferences_menu();
    });
  }
  return {load_ipython_extension : load_ipython_extension};
});
