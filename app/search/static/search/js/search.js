// search/static/search/js/search.js
class UniversalSearch {
    constructor(formElement) {
        this.form = formElement;
        this.resultsContainer = document.querySelector(`#results-${this.form.id}`);
        this.resultsList = this.resultsContainer.querySelector('.search-results-list');
        this.loadingElement = this.resultsContainer.querySelector('.search-loading');
        this.configId = this.form.dataset.configId;
        this.contentTypeId = this.form.dataset.contentType;
        this.resultsLimit = this.form.dataset.resultsLimit || 10;
        this.init();
    }
    
    async loadFieldChoices(fieldElement) {
        
        const fieldName = fieldElement.dataset.fieldName;
        const fieldType = fieldElement.dataset.fieldType;
        if (!['select', 'radio'].includes(fieldType)) {
            return;
        }
        
        try {
            const response = await fetch(
                `/search/api/field-choices/${this.configId}/${fieldElement.dataset.fieldId}/`
            );
            
            if (!response.ok) return;
            
            const data = await response.json();
            if (data.success && data.choices.length > 0) {
                this.populateFieldChoices(fieldElement, data.choices, fieldType);
            }
            
        } catch (error) {
            console.error('Error loading choices:', error);
        }
    }
    
    populateFieldChoices(fieldElement, choices, fieldType) {
        if (fieldType === 'select') {
            const select = fieldElement;
            if (select) {
                // Очищаем существующие опции кроме первой
                while (select.options.length > 1) {
                    select.remove(1);
                }
                
                // Добавляем новые опции
                choices.forEach(choice => {
                    const option = document.createElement('option');
                    option.value = choice.value;
                    option.textContent = choice.label;
                    select.appendChild(option);
                });
            }
        } else if (fieldType === 'radio') {
            const container = fieldElement;
            // Очищаем существующие радиокнопки
            container.innerHTML = `<label class="form-label">${fieldElement.dataset.label || 'Выберите'}</label>`;
            
            // Добавляем новые радиокнопки
            choices.forEach((choice, index) => {
                const radioId = `field_${fieldElement.dataset.fieldId}_${index}`;
                const radioHtml = `
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="radio" 
                               name="${fieldElement.dataset.fieldName}"
                               value="${choice.value}"
                               id="${radioId}">
                        <label class="form-check-label" for="${radioId}">
                            ${choice.label}
                        </label>
                    </div>
                `;
                container.insertAdjacentHTML('beforeend', radioHtml);
            });
        }
    }

    init() {
        // Событие отправки формы
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.performSearch();
        });
        
        // Событие очистки
        const clearBtn = this.form.querySelector('.search-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearSearch());
        }
        
        // Автопоиск при вводе
        const searchInput = this.form.querySelector('.search-input');
        if (searchInput) {
            let timeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    if (e.target.value.length >= 2) {
                        this.performSearch();
                    } else {
                        this.hideResults();
                    }
                }, 500);
            });
        }
        
        // Загружаем динамические choices для полей
        const dynamicFields = this.form.querySelectorAll('[data-field-type="select"], [data-field-type="radio"]');
        dynamicFields.forEach(field => {
            if (field.dataset.fieldId) {
                
                this.loadFieldChoices(field);
            }
        });
    }
    
    getFormData() {
        const formData = new FormData(this.form);
        const data = {};

        // Вспомогательная функция для парсинга значений
        const parseValue = (val) => {
            if (!val?.trim()) return null;
            const num = Number(val);
            return isNaN(num) ? val : num;
        };

        const parseDate = (val) => {
            if (!val?.trim()) return null;
            const str = val.trim();

            // Проверяем формат DD.MM.YYYY с помощью регулярного выражения
            const dateMatch = str.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
            
            if (dateMatch) {
                const [, day, month, year] = dateMatch;
                // Создаём дату в UTC, чтобы избежать проблем с часовыми поясами
                const date = new Date(Date.UTC(year, month - 1, day));
                
                // Проверяем, что дата корректна (например, не 32.13.2027)
                if (
                    date.getUTCFullYear() == year &&
                    date.getUTCMonth() == month - 1 &&
                    date.getUTCDate() == day
                ) {
                    // Форматируем как YYYY-MM-DD
                    const pad = (n) => n.toString().padStart(2, '0');
                    return `${year}-${pad(month)}-${pad(day)}`;
                }
            }

            // Если не дата — пробуем число
            const num = Number(str);
            if (!isNaN(num)) {
                return num;
            }

            // Иначе возвращаем строку
            return str;
        };

        const getScalar = (val) => (Array.isArray(val) ? val[val.length - 1] : val);

        // Собираем все поля из формы (single/multiple)
        for (const [key, value] of formData.entries()) {
            if (!value?.trim()) continue;

            if (data[key] === undefined) {
                data[key] = [value];
                continue;
            }

            if (Array.isArray(data[key])) {
                data[key].push(value);
            } else {
                data[key] = [data[key], value];
            }
        }

        // Обрабатываем rangeFields
        const rangeFields = this.form.querySelectorAll('[data-field-type="range"]');
        
        rangeFields.forEach(field => {
            let fieldName = field.dataset.fieldName;
            let minKey = `${fieldName}_min`;
            let maxKey = `${fieldName}_max`;

            // Извлекаем и парсим значения
            let minValue = data[minKey] !== undefined ? parseValue(getScalar(data[minKey])) : null;
            let maxValue = data[maxKey] !== undefined ? parseValue(getScalar(data[maxKey])) : null;

            // Если есть хотя бы одно значение, создаем массив и удаляем исходные поля
            if (minValue !== null || maxValue !== null) {
                delete data[minKey];
                delete data[maxKey];
                data[fieldName] = [minValue, maxValue];
            }
        });

        // Обрабатываем dateRangeFields
        const dateRangeFields = this.form.querySelectorAll('[data-field-type="date"]');
        
        dateRangeFields.forEach(field => {
            let fieldName = field.dataset.fieldName;
            let minKey = `${fieldName}_min`;
            let maxKey = `${fieldName}_max`;

            // Извлекаем и парсим значения
            let minValue = data[minKey] !== undefined ? parseDate(getScalar(data[minKey])) : null;
            let maxValue = data[maxKey] !== undefined ? parseDate(getScalar(data[maxKey])) : null;

            // Если есть хотя бы одно значение, создаем массив и удаляем исходные поля
            if (minValue !== null || maxValue !== null) {
                delete data[minKey];
                delete data[maxKey];
                data[fieldName] = [minValue, maxValue];
            }
        });

        // // Преобразуем значения: парсим и приводим multiple к массиву
        // for (const key in data) {
        //     if (Array.isArray(data[key])) {
        //         // Multiple select: парсим каждое значение
        //         data[key] = data[key].filter(v => typeof v === 'string' && v.trim() !== '');
        //     } else {
        //         // Single select или input
        //         data[key] = parseValue(data[key]);
        //     }
        // }

        return data;
    }
    
    async performSearch() {
        const data = this.getFormData();
        console.log('Search data:', data);
        // Показываем загрузку
        this.showLoading();
        this.showResults();
        try {
            const response = await fetch('/search/api/search/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                },
                body: JSON.stringify({
                    config_id: this.configId,
                    content_type_id: this.contentTypeId,
                    search_data: data,
                    limit: this.resultsLimit
                })
            });
            
            if (!response.ok) throw new Error('Ошибка поиска');
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Search error:', error);
            this.displayError('Ошибка при выполнении поиска');
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(result) {
        this.resultsList.innerHTML = '';
        
        if (!result.success) {
            this.displayError(result.message || 'Ошибка поиска');
            return;
        }
        
        if (result.results.length === 0) {
            this.resultsList.innerHTML = `
                <div class="alert alert-info m-2">
                    Ничего не найдено
                </div>
            `;
            return;
        }
        
        // Показываем количество результатов
        if (result.show_count) {
            const countHtml = `
                <div class="search-results-count p-2 border-bottom">
                    <small class="text-muted">Найдено: ${result.total}</small>
                </div>
            `;
            this.resultsList.innerHTML = countHtml;
        }
        
        // Добавляем результаты
        result.results.forEach(item => {
            const resultItem = document.createElement('div');
            resultItem.className = 'search-result-item';
            resultItem.dataset.objectId = item.id;
            resultItem.dataset.objectType = item.content_type;
            resultItem.innerHTML = this.formatResultItem(item);
            
            // Событие клика
            resultItem.addEventListener('click', () => {
                this.onResultClick(item);
            });
            
            this.resultsList.appendChild(resultItem);
        });
        
        // Кнопка "Показать все"
        if (result.has_more) {
            const showAllBtn = document.createElement('button');
            showAllBtn.className = 'btn btn-link btn-sm w-100 text-center';
            showAllBtn.textContent = 'Показать все...';
            showAllBtn.addEventListener('click', () => this.showAllResults(result.search_id));
            this.resultsList.appendChild(showAllBtn);
        }
    }
    
    formatResultItem(item) {
        // Кастомизируйте отображение под ваши нужды
        return `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>${item.title || `Объект #${item.id}`}</strong>
                    ${item.description ? `<div class="small text-muted">${item.description}</div>` : ''}
                </div>
                <span class="badge bg-secondary">ID: ${item.id}</span>
            </div>
        `;
    }
    
    onResultClick(item) {
        // Событие при клике на результат
        const event = new CustomEvent('search-result-click', {
            detail: {
                id: item.id,
                content_type: item.content_type,
                object: item,
                config_id: this.configId
            },
            bubbles: true
        });
        this.form.dispatchEvent(event);
        
        // По умолчанию - переход на страницу объекта
        if (item.url) {
            window.location.href = item.url;
        }
    }
    
    showAllResults(searchId) {
        // Загрузить все результаты
        console.log('Show all for search:', searchId);
    }
    
    showLoading() {
        this.loadingElement.style.display = 'block';
    }
    
    hideLoading() {
        this.loadingElement.style.display = 'none';
    }
    
    showResults() {
        this.resultsContainer.style.display = 'block';
    }
    
    hideResults() {
        this.resultsContainer.style.display = 'none';
    }
    
    clearSearch() {
        this.form.reset();
        this.hideResults();
        this.resultsList.innerHTML = '';
    }
    
    displayError(message) {
        this.resultsList.innerHTML = `
            <div class="alert alert-danger m-2">
                ${message}
            </div>
        `;
    }
    
    getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
}

// Инициализация всех форм поиска на странице
document.addEventListener('DOMContentLoaded', function() {
    const searchForms = document.querySelectorAll('.search-form');
    searchForms.forEach(form => {
        new UniversalSearch(form);
    });
});
