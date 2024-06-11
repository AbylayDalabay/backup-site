$(document).ready(function() {
    var originalValues = {};
    var userRole;

    // Fetch user info to update profile section and get user role
    fetch('/get_user_info')
        .then(response => response.json())
        .then(data => { 
            if (data.success) {
                document.querySelector('.profile-circle').textContent = data.user.login[0].toUpperCase();
                document.querySelector('.profile-name').textContent = data.user.login;
                userRole = data.user.role;  // Store user role
            }
        });

    function fetchTableContent(language, table) {
        $.ajax({
            type: 'POST',
            url: '/get_table_content',
            contentType: 'application/json',
            data: JSON.stringify({ language: language, table: table }),
            success: function(response) {
                displayTableContent(response.columns, response.content);
            }
        });
    }

    function fetchBackupContent(language, table, backup) {
        $.ajax({
            type: 'POST',
            url: '/get_backup_content',
            contentType: 'application/json',
            data: JSON.stringify({ language: language, table: table, backup: backup }),
            success: function(response) {
                displayTableContent(response.columns, response.content);
            }
        });
    }

    function displayTableContent(headers, content) {
        if ($.fn.DataTable.isDataTable('#table-content')) {
            $('#table-content').DataTable().destroy();
        }

        $('#table-headers').empty();
        $('#table-rows').empty();
        originalValues = {};

        $.each(headers, function(index, header) {
            $('#table-headers').append('<th>' + header + '</th>');
        });
        $('#table-headers').append('<th>Действие</th>');

        $.each(content, function(index, row) {
            var rowHtml = '<tr>';
            $.each(row, function(i, cell) {
                var cellId = 'row-' + index + '-col-' + i;
                var contentEditable = userRole === 'editor' ? 'contenteditable="true"' : '';  // Allow editing only for editors
                rowHtml += '<td id="' + cellId + '" ' + contentEditable + ' data-column="' + headers[i] + '" data-row-id="' + row[0] + '">' + cell + '</td>';
                originalValues[cellId] = cell;
            });
            rowHtml += '<td><button class="delete-row" data-row-id="' + row[0] + '">Удалить</button></td>';
            rowHtml += '</tr>';
            $('#table-rows').append(rowHtml);
        });

        $('#table-content').DataTable();
    }

    function fetchBackups(language, table) {
        $.ajax({
            type: 'POST',
            url: '/get_backups',
            contentType: 'application/json',
            data: JSON.stringify({ language: language, table: table }),
            success: function(response) {
                $('#backup').empty().append('<option value="">--Не Выбрано--</option>');
                $.each(response, function(index, backup) {
                    $('#backup').append('<option value="' + backup + '">' + backup + '</option>');
                });
            }
        });
    }

    function showNotification(message, type) {
        var notification = $('#notification');
        notification.removeClass('hidden').removeClass('success error duplicate').addClass(type).text(message);
        setTimeout(function() {
            notification.addClass('hidden');
        }, 3000);
    }

    $('#language').change(function() {
        var language = $(this).val();
        $.ajax({
            type: 'POST',
            url: '/get_tables',
            contentType: 'application/json',
            data: JSON.stringify({ language: language }),
            success: function(response) {
                $('#table').empty().append('<option value="">--Выбрать Таблицу--</option>');
                $.each(response, function(index, table) {
                    $('#table').append('<option value="' + table + '">' + table + '</option>');
                });
            }
        });
    });

    $('#table').change(function() {
        var language = $('#language').val();
        var table = $(this).val();
        if (language && table) {
            $('#insert-section').removeClass('hidden');
            $('#toggle-insert-section').text('Скрыть Раздел Вставки');
            $('#table-section').removeClass('hidden');
            $('#toggle-table-section').text('Скрыть Раздел Таблицы');
            $('#search-section').removeClass('hidden');
            $('#toggle-search-section').text('Скрыть Раздел Поиска');
            fetchTableContent(language, table);
            fetchBackups(language, table);
        } else {
            $('#insert-section').addClass('hidden');
            $('#table-section').addClass('hidden');
            $('#search-section').addClass('hidden');
        }
    });

    $('#backup').change(function() {
        var language = $('#language').val();
        var table = $('#table').val();
        var backup = $(this).val();
        if (backup === "") {
            fetchTableContent(language, table);
        } else if (language && table && backup) {
            fetchBackupContent(language, table, backup);
        }
    });

    $('#restore-button').click(function() {
        var language = $('#language').val();
        var table = $('#table').val();
        var backup = $('#backup').val();
        if (language && table && backup) {
            $.ajax({
                type: 'POST',
                url: '/restore_backup',
                contentType: 'application/json',
                data: JSON.stringify({ language: language, table: table, backup: backup }),
                success: function(response) {
                    if (response.success) {
                        fetchTableContent(language, table);
                        showNotification('Восстановление успешно', 'success');
                    } else {
                        showNotification('Восстановление не удалось', 'error');
                    }
                }
            });
        }
    });

    $('#show-current-button').click(function() {
        var language = $('#language').val();
        var table = $('#table').val();
        if (language && table) {
            fetchTableContent(language, table);
        }
    });

    $(document).on('blur', 'td[contenteditable="true"]', function() {
        var cellId = $(this).attr('id');
        var new_value = $(this).text();
        var original_value = originalValues[cellId];
        
        if (new_value !== original_value) {
            var column = $(this).data('column');
            var row_id = $(this).data('row-id');
            var language = $('#language').val();
            var table = $('#table').val();
            $.ajax({
                type: 'POST',
                url: '/update_cell',
                contentType: 'application/json',
                data: JSON.stringify({ language: language, table: table, column: column, row_id: row_id, new_value: new_value }),
                success: function(response) {
                    if (response.success) {
                        originalValues[cellId] = new_value;
                        fetchBackups(language, table);
                        showNotification('Обновление успешно', 'success');
                    } else {
                        showNotification('Обновление не удалось', 'error');
                    }
                }
            });
        }
    });

    $(document).on('click', '.delete-row', function() {
        var row_id = $(this).data('row-id');
        var language = $('#language').val();
        var table = $('#table').val();
        $.ajax({
            type: 'POST',
            url: '/delete_row',
            contentType: 'application/json',
            data: JSON.stringify({ language: language, table: table, row_id: row_id }),
            success: function(response) {
                if (response.success) {
                    fetchTableContent(language, table);
                    fetchBackups(language, table);
                    showNotification('Удаление успешно', 'success');
                } else {
                    showNotification('Удаление не удалось', 'error');
                }
            }
        });
    });

    $('#insert-form').submit(function(event) {
        event.preventDefault();
        var question = $('#question').val();
        var answer = $('#answer').val();
        var data_type = $('#data_type').val();
        var language = $('#language').val();
        var table = $('#table').val();
        if (language && table && question && answer) {
            $.ajax({
                type: 'POST',
                url: '/get_last_row_id',
                contentType: 'application/json',
                data: JSON.stringify({ language: language, table: table }),
                success: function(response) {
                    var question_id = response.last_row_id + 1;
                    var new_data = [{ question: question, answer: answer, question_id: question_id, data_type: data_type }];
                    $.ajax({
                        type: 'POST',
                        url: '/insert_data',
                        contentType: 'application/json',
                        data: JSON.stringify({ language: language, table: table, data: new_data }),
                        success: function(response) {
                            if (response.success) {
                                fetchTableContent(language, table);
                                fetchBackups(language, table);  // Refresh backups select box
                                if (response.duplicate) {
                                    showNotification('Вставка успешна, но вопрос уже существует', 'duplicate');
                                } else {
                                    showNotification('Вставка успешна', 'success');
                                }
                            } else {
                                showNotification('Вставка не удалась', 'error');
                            }
                        }
                    });
                }
            });
        }
    });

    $('#toggle-json-section').click(function() {
        $('#json-section').toggle();
    });

    $('#insert-json-button').click(function() {
        var jsonInput = $('#json-input').val();
        var language = $('#language').val();
        var table = $('#table').val();
        try {
            var jsonData = JSON.parse(jsonInput);
            if (Array.isArray(jsonData) && jsonData.length > 0) {
                $.ajax({
                    type: 'POST',
                    url: '/insert_json',
                    contentType: 'application/json',
                    data: JSON.stringify({ language: language, table: table, data: jsonData }),
                    success: function(response) {
                        if (response.success) {
                            fetchTableContent(language, table);
                            fetchBackups(language, table);
                            if (response.duplicate) {
                                showNotification('Вставка JSON успешна, но некоторые вопросы уже существуют', 'duplicate');
                            } else {
                                showNotification('Вставка JSON успешна', 'success');
                            }
                        } else {
                            showNotification('Вставка JSON не удалась', 'error');
                        }
                    }
                });
            } else {
                alert('Неверный формат JSON');
            }
        } catch (e) {
            alert('Неверный формат JSON');
        }
    });

    $('#toggle-insert-section').click(function() {
        var buttonText = $(this).text();
        if (buttonText === 'Скрыть Раздел Вставки') {
            $('#insert-section .section-content').hide();
            $(this).text('Показать Раздел Вставки');
        } else {
            $('#insert-section .section-content').show();
            $(this).text('Скрыть Раздел Вставки');
        }
    });

    $('#toggle-search-section').click(function() {
        var buttonText = $(this).text();
        if (buttonText === 'Скрыть Раздел Поиска') {
            $('#search-section .section-content').hide();
            $(this).text('Показать Раздел Поиска');
        } else {
            $('#search-section .section-content').show();
            $(this).text('Скрыть Раздел Поиска');
        }
    });

    $('#toggle-table-section').click(function() {
        var buttonText = $(this).text();
        if (buttonText === 'Скрыть Раздел Таблицы') {
            $('#table-section .section-content').hide();
            $(this).text('Показать Раздел Таблицы');
        } else {
            $('#table-section .section-content').show();
            $(this).text('Скрыть Раздел Таблицы');
        }
    });

    $('#search-form').submit(function(event) {
        event.preventDefault();
        var query = $('#query').val();
        var table_type = $('#table').val();
        if (query && table_type) {
            $.ajax({
                type: 'POST',
                url: '/search',
                contentType: 'application/json',
                data: JSON.stringify({ query: query, table_type: table_type }),
                success: function(response) {
                    if (response.success) {
                        var searchResults = response.results;
                        if (searchResults.length > 0) {
                            var tableHtml = '<table class="data"><thead><tr>';
                            $.each(Object.keys(searchResults[0]), function(index, key) {
                                tableHtml += '<th>' + key + '</th>';
                            });
                            tableHtml += '</tr></thead><tbody>';
                            $.each(searchResults, function(index, row) {
                                tableHtml += '<tr>';
                                $.each(row, function(key, value) {
                                    tableHtml += '<td>' + value + '</td>';
                                });
                                tableHtml += '</tr>';
                            });
                            tableHtml += '</tbody></table>';
                            $('#search-results').html(tableHtml);
                        } else {
                            $('#search-results').html('Результаты не найдены');
                        }
                    } else {
                        $('#search-results').html('Произошла ошибка при получении результатов.');
                    }
                }
            });
        }
    });

    $('#clear-results').click(function() {
        $('#search-results').empty();
    });

    $('#language').trigger('change');

    // Attach logout function to the button
    document.getElementById('logout-button').addEventListener('click', function() {
        fetch('/logout').then(() => location.reload());
    });
});
