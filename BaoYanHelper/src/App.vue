<template>
  <div class="app">
    <!-- 导航栏 -->
    <header class="navbar">
      <div class="navbar__container">
        <div class="navbar__left">
          <div class="navbar__logo">
            <h1>HustOJ</h1>
          </div>
          <nav class="navbar__nav">
            <a href="#" class="navbar__link active">题库</a>
            <a href="#" class="navbar__link">比赛</a>
            <a href="#" class="navbar__link">讨论</a>
            <a href="#" class="navbar__link">排行榜</a>
            <a href="#" class="navbar__link">学习</a>
          </nav>
        </div>
        <div class="navbar__right">
          <div class="navbar__search">
            <input type="text" placeholder="搜索题目..." class="navbar__search-input">
            <button class="navbar__search-btn">🔍</button>
          </div>
          <div class="navbar__user">
            <button class="navbar__user-btn">登录</button>
            <button class="navbar__user-btn navbar__user-btn--primary">注册</button>
          </div>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="main">
      <div class="main__container">
        <!-- 左侧筛选栏 -->
        <aside class="sidebar">
          <div class="sidebar__section">
            <h3 class="sidebar__title">难度</h3>
            <ul class="sidebar__list">
              <li class="sidebar__item">
                <input type="checkbox" id="easy" class="sidebar__checkbox">
                <label for="easy" class="sidebar__label">简单</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="medium" class="sidebar__checkbox">
                <label for="medium" class="sidebar__label">中等</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="hard" class="sidebar__checkbox">
                <label for="hard" class="sidebar__label">困难</label>
              </li>
            </ul>
          </div>
          
          <div class="sidebar__section">
            <h3 class="sidebar__title">标签</h3>
            <ul class="sidebar__list">
              <li class="sidebar__item">
                <input type="checkbox" id="array" class="sidebar__checkbox">
                <label for="array" class="sidebar__label">数组</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="string" class="sidebar__checkbox">
                <label for="string" class="sidebar__label">字符串</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="dp" class="sidebar__checkbox">
                <label for="dp" class="sidebar__label">动态规划</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="tree" class="sidebar__checkbox">
                <label for="tree" class="sidebar__label">树</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="graph" class="sidebar__checkbox">
                <label for="graph" class="sidebar__label">图</label>
              </li>
            </ul>
          </div>
          
          <div class="sidebar__section">
            <h3 class="sidebar__title">状态</h3>
            <ul class="sidebar__list">
              <li class="sidebar__item">
                <input type="checkbox" id="accepted" class="sidebar__checkbox">
                <label for="accepted" class="sidebar__label">已通过</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="submitted" class="sidebar__checkbox">
                <label for="submitted" class="sidebar__label">已提交</label>
              </li>
              <li class="sidebar__item">
                <input type="checkbox" id="not-started" class="sidebar__checkbox">
                <label for="not-started" class="sidebar__label">未开始</label>
              </li>
            </ul>
          </div>
        </aside>

        <!-- 右侧题目列表 -->
        <div class="problems">
          <div class="problems__header">
            <h2 class="problems__title">题库</h2>
            <div class="problems__actions">
              <select class="problems__select">
                <option>按最新排序</option>
                <option>按难度排序</option>
                <option>按通过率排序</option>
              </select>
            </div>
          </div>
          
          <div class="problems__list">
            <div class="problem__item">
              <div class="problem__info">
                <div class="problem__number">1.</div>
                <div class="problem__details">
                  <h3 class="problem__title">两数之和</h3>
                  <div class="problem__tags">
                    <span class="problem__tag">简单</span>
                    <span class="problem__tag">数组</span>
                    <span class="problem__tag">哈希表</span>
                  </div>
                </div>
              </div>
              <div class="problem__status">
                <span class="problem__pass-rate">通过率: 45.2%</span>
                <button class="problem__solve-btn">开始解答</button>
              </div>
            </div>
            
            <div class="problem__item">
              <div class="problem__info">
                <div class="problem__number">2.</div>
                <div class="problem__details">
                  <h3 class="problem__title">两数相加</h3>
                  <div class="problem__tags">
                    <span class="problem__tag problem__tag--medium">中等</span>
                    <span class="problem__tag">链表</span>
                    <span class="problem__tag">数学</span>
                  </div>
                </div>
              </div>
              <div class="problem__status">
                <span class="problem__pass-rate">通过率: 36.7%</span>
                <button class="problem__solve-btn">开始解答</button>
              </div>
            </div>
            
            <div class="problem__item">
              <div class="problem__info">
                <div class="problem__number">3.</div>
                <div class="problem__details">
                  <h3 class="problem__title">无重复字符的最长子串</h3>
                  <div class="problem__tags">
                    <span class="problem__tag problem__tag--medium">中等</span>
                    <span class="problem__tag">字符串</span>
                    <span class="problem__tag">滑动窗口</span>
                  </div>
                </div>
              </div>
              <div class="problem__status">
                <span class="problem__pass-rate">通过率: 34.1%</span>
                <button class="problem__solve-btn">开始解答</button>
              </div>
            </div>
            
            <div class="problem__item">
              <div class="problem__info">
                <div class="problem__number">4.</div>
                <div class="problem__details">
                  <h3 class="problem__title">寻找两个正序数组的中位数</h3>
                  <div class="problem__tags">
                    <span class="problem__tag problem__tag--hard">困难</span>
                    <span class="problem__tag">数组</span>
                    <span class="problem__tag">二分查找</span>
                  </div>
                </div>
              </div>
              <div class="problem__status">
                <span class="problem__pass-rate">通过率: 38.4%</span>
                <button class="problem__solve-btn">开始解答</button>
              </div>
            </div>
            
            <div class="problem__item">
              <div class="problem__info">
                <div class="problem__number">5.</div>
                <div class="problem__details">
                  <h3 class="problem__title">最长回文子串</h3>
                  <div class="problem__tags">
                    <span class="problem__tag problem__tag--medium">中等</span>
                    <span class="problem__tag">字符串</span>
                    <span class="problem__tag">动态规划</span>
                  </div>
                </div>
              </div>
              <div class="problem__status">
                <span class="problem__pass-rate">通过率: 33.5%</span>
                <button class="problem__solve-btn">开始解答</button>
              </div>
            </div>
          </div>
          
          <div class="problems__pagination">
            <button class="pagination__btn">上一页</button>
            <button class="pagination__btn pagination__btn--active">1</button>
            <button class="pagination__btn">2</button>
            <button class="pagination__btn">3</button>
            <button class="pagination__btn">...</button>
            <button class="pagination__btn">100</button>
            <button class="pagination__btn">下一页</button>
          </div>
        </div>
      </div>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="footer__container">
        <div class="footer__links">
          <a href="#" class="footer__link">关于我们</a>
          <a href="#" class="footer__link">联系我们</a>
          <a href="#" class="footer__link">使用条款</a>
          <a href="#" class="footer__link">隐私政策</a>
        </div>
        <div class="footer__copyright">
          © 2024 HustOJ. All rights reserved.
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
// 组件逻辑
</script>

<style scoped>
/* 组件样式 */
</style>