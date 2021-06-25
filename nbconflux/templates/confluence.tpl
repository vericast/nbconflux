{%- extends 'display_priority.j2' -%}
{% from 'mathjax.html.j2' import mathjax %}

{%- block header -%}
{%- if resources.generate_toc %}
<ac:structured-macro ac:macro-id="dca3b6c0-062d-415e-bfcd-67ea8153e627" ac:name="toc" ac:schema-version="1">
    <ac:parameter ac:name="maxLevel">3</ac:parameter>
    <ac:parameter ac:name="indent">15px</ac:parameter>
</ac:structured-macro>
{%- endif %}
{%- endblock header %}

{% block codecell %}
<p class="border-box-sizing code_cell rendered">
{{ super() }}
</p>
{%- endblock codecell %}

{% block input_group -%}
<div class="input">
{{ super() }}
</div>
{% endblock input_group %}

{% block output_group %}
<div class="output_wrapper">
<div class="output">
{{ super() }}
</div>
</div>
{% endblock output_group %}

{% block in_prompt -%}
<div class="prompt input_prompt">
{%- if cell.execution_count is defined -%}
{%- if resources.global_content_filter.include_input_prompt-%}
In&nbsp;[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
{%- else -%}
In&nbsp;[&nbsp;]:
{%- endif -%}
{%- endif -%}
</div>
{%- endblock in_prompt %}

{% block empty_in_prompt -%}
{%- if resources.global_content_filter.include_input_prompt-%}
<div class="prompt input_prompt">
</div>
{% endif %}
{%- endblock empty_in_prompt %}

{# 
  output_prompt doesn't do anything in HTML,
  because there is a prompt div in each output area (see output block)
#}
{% block output_prompt %}
{% endblock output_prompt %}

{% block input %}
<div class="inner_cell">
    <div class="input_area">
{{ cell.source | highlight_code(metadata=cell.metadata) }}
</div>
</div>
{%- endblock input %}

{% block output %}
<div class="output_area">
{% if resources.global_content_filter.include_output_prompt %}
{% block output_area_prompt %}
{%- if output.output_type == 'execute_result' -%}
    <div class="prompt output_prompt">
{%- if cell.execution_count is defined -%}
    Out[{{ cell.execution_count|replace(None, "&nbsp;") }}]:
{%- else -%}
    Out[&nbsp;]:
{%- endif -%}
{%- else -%}
    <div class="prompt">
{%- endif -%}
    </div>
{% endblock output_area_prompt %}
{% endif %}
{{ super() }}
</div>
{% endblock output %}

{% block markdowncell scoped %}
<div class="border-box-sizing text_cell rendered">
{%- if resources.global_content_filter.include_input_prompt-%}
{{ self.empty_in_prompt() }}
{%- endif -%}
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html">
{{ cell.source  | markdown2html | strip_files_prefix | sanitize_html }}
</div>
</div>
</div>
{%- endblock markdowncell %}

{% block unknowncell scoped %}
unknown type  {{ cell.type }}
{% endblock unknowncell %}

{% block execute_result -%}
{%- set extra_class="output_execute_result" -%}
{% block data_priority scoped %}
{{ super() }}
{% endblock %}
{%- set extra_class="" -%}
{%- endblock execute_result %}

{% block stream_stdout -%}
<div class="output_subarea output_stream output_stdout output_text">
<pre>
{{- output.text | ansi2html | sanitize_html -}}
</pre>
</div>
{%- endblock stream_stdout %}

{% block stream_stderr -%}
<div class="output_subarea output_stream output_stderr output_text">
<pre>
{{- output.text | ansi2html | sanitize_html -}}
</pre>
</div>
{%- endblock stream_stderr %}

{% block data_svg scoped -%}
<div class="output_svg output_subarea {{ extra_class }}">SVG is not supported</div>
{%- endblock data_svg %}

{% block data_html scoped -%}
<div class="output_html rendered_html output_subarea {{ extra_class }}">
{{ output.data['text/html'] | sanitize_html }}
</div>
{%- endblock data_html %}

{% block data_markdown scoped -%}
<div class="output_markdown rendered_html output_subarea {{ extra_class }}">
{{ output.data['text/markdown'] | markdown2html | sanitize_html }}
</div>
{%- endblock data_markdown %}

{% block data_png scoped %}
<div class="output_png output_subarea {{ extra_class }}">
{%- if 'image/png' in output.metadata.get('filenames', {}) %}
<ac:image><ri:url ri:value="{{ resources['attachments'][output.metadata.filenames['image/png']][2] }}" /></ac:image>
{%- endif %}
</div>
{%- endblock data_png %}

{% block data_jpg scoped %}
<div class="output_jpeg output_subarea {{ extra_class }}">
{%- if 'image/jpeg' in output.metadata.get('filenames', {}) %}
<ac:image><ri:url ri:value="{{ resources['attachments'][output.metadata.filenames['image/jpeg']][2] }}" /></ac:image>
{%- endif %}
</div>
{%- endblock data_jpg %}

{% block data_latex scoped %}
<div class="output_latex output_subarea {{ extra_class }}">
{{ output.data['text/latex'] }}
</div>
{%- endblock data_latex %}

{% block error -%}
<div class="output_subarea output_text output_error">
<pre>
{{- super() -}}
</pre>
</div>
{%- endblock error %}

{%- block traceback_line %}
{{ line | ansi2html | sanitize_html }}
{%- endblock traceback_line %}

{%- block data_text scoped %}
<div class="output_text output_subarea {{ extra_class }}">
<pre>
{{- output.data['text/plain'] | ansi2html | sanitize_html -}}
</pre>
</div>
{%- endblock -%}

{%- block data_javascript scoped %}
<div class="output_subarea output_javascript {{ extra_class }}">Custom JavaScript is not supported</div>
{%- endblock -%}

{%- block data_widget_state scoped %}
{%- endblock data_widget_state -%}

{%- block data_widget_view scoped %}
<div class="output_subarea output_widget_view {{ extra_class }}">Widgets are not supported</div>
{%- endblock data_widget_view -%}

{%- block footer %}
{{ super() }}
{%- if 'notebook_filename' in resources %}
<hr />
<p><em>This page originated from the notebook <a href="{{ resources['attachments'][resources['notebook_filename']]['download_url'] }}">{{ resources['notebook_filename'] }}</a> which is attached to this page for safe keeping.</em></p>
{%- endif %}

<ac:structured-macro ac:macro-id="8250dedf-fcaa-48da-b12d-0f929c620dc4" ac:name="style" ac:schema-version="1">
    <ac:parameter ac:name="import">https://nbviewer.jupyter.org/static/build/notebook.css</ac:parameter>
</ac:structured-macro>

<ac:structured-macro ac:macro-id="8250dedf-fcaa-48da-b12d-0f929c620dc4" ac:name="style" ac:schema-version="1">
    <ac:plain-text-body><![CDATA[
        a.anchor-link {
            display: none !important;
        }
        body div.output_subarea {
            max-width: none;
        }
        body.page-gadget #main {
            width: auto;
        }
        body.page-gadget {
            padding-top: 0;
        }
        ]]>
    </ac:plain-text-body>
</ac:structured-macro>

{%- if resources.enable_mathjax %}
<ac:structured-macro ac:macro-id="c5e95bac-43c5-4db4-abd0-af1dfcf97384" ac:name="html" ac:schema-version="1">
    <ac:plain-text-body><![CDATA[
        {{ mathjax() }}
    ]]>
</ac:plain-text-body></ac:structured-macro>
{%- endif %}

{%- endblock footer-%}