document.addEventListener('DOMContentLoaded', function() {
    console.log('Wechat Chat Main Interface Loaded');
    
    // 这里可以添加一些交互逻辑
    const cards = document.querySelectorAll('.entry-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.borderColor = '#009688';
        });
        card.addEventListener('mouseleave', function() {
            this.style.borderColor = 'transparent';
        });
    });
});
