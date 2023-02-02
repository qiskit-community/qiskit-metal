$.ajaxSetup({ xhrFields: { withCredentials: true } });

define([
    'jquery',
    'base/js/utils',
    'base/js/events',
    'services/config',
    'nbextensions/jupyter_nbgallery/instrumentation/md5'
], function(
    $,
    utils,
    events,
    configmod,
    crypto
) {
    function load_ipython_extension() {
        var config = new configmod.ConfigSection('common', {base_url: utils.get_body_data("baseUrl")});
        config.load();

        // Post the client name/url to the gallery as an environment
        config.loaded.then(function() {
            var nbgallery = config['data'].nbgallery;
            // 'base' is the "home" nbgallery that's configured for this Jupyter instance
            var base = nbgallery.url;

            // Handle execution requests
            events.on('execute.CodeCell', function (evt, data) {
                // Add current time to the cell
                var cell = data.cell;
                cell.start_time = new Date().getTime();
                console.log('execute: ' + cell.toJSON().source.substr(0, 70) + '...');
            });

            // Handle execution completion
            events.on('finished_execute.CodeCell', function (evt, data) {
                var cell = data.cell;

                // Prevent getting called twice for the same execution
                if (cell.start_time == undefined) {
                    return;
                }

                // Populate cell execution data
                var log = {};
                log['runtime'] = ((new Date().getTime()) - cell.start_time) / 1000.0;
                cell.start_time = undefined;
                log['md5'] = CryptoJS.MD5(cell.toJSON().source).toString();
                log['success'] = true;
                log['uuid'] = undefined;

                outputs = cell.output_area.outputs;
                for(i in outputs) {
                    if(outputs[i].output_type == 'error') {
                        log['success'] = false;
                    }
                }

                // Post to gallery
                var gallery_metadata = Jupyter.notebook.metadata.gallery;
                var notebook_base = base;
                if (gallery_metadata) {
                    log['uuid'] = gallery_metadata.uuid || gallery_metadata.link || gallery_metadata.clone;
                    // If this notebook didn't come from the "home" gallery, send
                    // the log to the gallery it was launched from.
                    if (gallery_metadata.gallery_url) {
                        notebook_base = gallery_metadata.gallery_url;
                    }
                }
                console.log('finished_execute: ' + cell.toJSON().source.substr(0, 70) + '...');
                console.log(log);
                if (log['uuid'] != undefined) {
                    $.ajax({
                        method: 'POST',
                        headers: { Accept: 'application/json' },
                        url: notebook_base + "/executions",
                        data: log,
                        xhrFields: { withCredentials: true }
                    });
                }
            });
        });
    }

    return {load_ipython_extension : load_ipython_extension};
});
