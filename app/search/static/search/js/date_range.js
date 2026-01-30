// Функция инициализации datepicker для всех полей
(function() {
    // Настройки для календаря
    const options = {
        format: 'dd.mm.yyyy',
        language: 'ru',
        autoclose: true
    };
    
    // Для каждого блока date-range-group
    $('.date-range-group').each(function() {
        const $range = $(this);
        const $start = $range.find('.date-start');
        const $end = $range.find('.date-end');
        
        // Инициализируем datepicker
        $start.datepicker(options);
        $end.datepicker(options);
        
        // Делаем валидацию: конец не может быть раньше начала
        $start.on('changeDate', function(e) {
            $end.datepicker('setStartDate', e.date);
        });
        
        $end.on('changeDate', function(e) {
            $start.datepicker('setEndDate', e.date);
        });
    });
    // $('.date-range').each(function(index) {
    //     const start = $(this).find('.date-start').val();
    //     const end = $(this).find('.date-end').val();
        
    //     if (start || end) {
    //         hasData = true;
    //         result += `<p>Диапазон ${index + 1}: <strong>${start || 'не выбрано'}</strong> - <strong>${end || 'не выбрано'}</strong></p>`;
    //     }
    // });
}());