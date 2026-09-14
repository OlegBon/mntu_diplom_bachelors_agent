const gulp = require("gulp");
const pug = require("gulp-pug");
const sass = require("gulp-sass")(require("sass"));
const browserSync = require("browser-sync").create();
const plumber = require("gulp-plumber");
const notify = require("gulp-notify");
const autoprefixer = require("gulp-autoprefixer");
const del = require("del");

// Шляхи
const paths = {
  pug: {
    src: "src/pug/pages/*.pug", // Компілюємо тільки сторінки (не layout)
    dest: "dist/",
    watch: "src/pug/**/*.pug",
  },
  scss: {
    src: "src/scss/main.scss",
    dest: "dist/css/",
    watch: "src/scss/**/*.scss",
  },
  js: {
    src: "src/js/**/*.js",
    dest: "dist/js/",
    watch: "src/js/**/*.js",
  },
  img: {
    src: "src/img/**/*",
    dest: "dist/img/",
    watch: "src/img/**/*",
  },
};

// Обробка помилок (щоб Gulp не падав при помилці в коді)
const onError = function (err) {
  notify.onError({
    title: "Gulp Error",
    message: "Error: <%= error.message %>",
    sound: "Beep",
  })(err);
  this.emit("end");
};

// Компіляція PUG -> HTML
function html() {
  return gulp
    .src(paths.pug.src)
    .pipe(plumber({ errorHandler: onError }))
    .pipe(pug({ pretty: true })) // pretty: true робить HTML читабельним
    .pipe(gulp.dest(paths.pug.dest))
    .pipe(browserSync.stream());
}

// Компіляція SCSS -> CSS
function styles() {
  return gulp
    .src(paths.scss.src)
    .pipe(plumber({ errorHandler: onError }))
    .pipe(sass().on("error", sass.logError))
    .pipe(
      autoprefixer({
        cascade: false,
        grid: true,
      }),
    )
    .pipe(gulp.dest(paths.scss.dest))
    .pipe(browserSync.stream());
}

// Копіювання JS (можна додати мініфікацію, поки просто копіюємо)
function scripts() {
  return gulp
    .src(paths.js.src)
    .pipe(gulp.dest(paths.js.dest))
    .pipe(browserSync.stream());
}

// Картинки
function images() {
  return gulp
    // Gulp 5 decodes source files as UTF-8 unless binary mode is explicit.
    // Images must stay byte-for-byte intact when copied to dist.
    .src(paths.img.src, { allowEmpty: true, encoding: false })
    .pipe(gulp.dest(paths.img.dest));
}

// Локальний сервер
function server() {
  browserSync.init({
    server: {
      baseDir: "./dist",
    },
    port: 3000,
    notify: false,
  });
}

// Слідкування за змінами
function watchFiles() {
  gulp.watch(paths.pug.watch, html);
  gulp.watch(paths.scss.watch, styles);
  gulp.watch(paths.js.watch, scripts);
  gulp.watch(paths.img.watch, images);
}

// Очищення папки dist
function clean() {
  return del(["dist"]);
}

// Експорт завдань
const build = gulp.series(clean, gulp.parallel(html, styles, scripts, images));
const defaultTask = gulp.series(build, gulp.parallel(watchFiles, server));

exports.html = html;
exports.styles = styles;
exports.clean = clean;
exports.build = build;
exports.default = defaultTask;
